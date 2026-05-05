"""
Authentication views: register, login (email+password), refresh, logout,
profile, preferences, and Google OAuth code exchange.
"""

from __future__ import annotations

import logging

import requests
from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView  # noqa: F401  (re-export)

from .serializers import (
    PasswordChangeSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    PreferencesSerializer,
    RegisterSerializer,
    TokenPairSerializer,
    UserSerializer,
)

logger = logging.getLogger("lankaguide.accounts")

User = get_user_model()


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        ser = RegisterSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = ser.save()
        return Response(
            TokenPairSerializer.for_user(user),
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = (request.data.get("email") or "").strip().lower()
        username = (request.data.get("username") or "").strip()
        password = request.data.get("password") or ""
        if not password or (not email and not username):
            return Response(
                {"detail": "Username/email and password are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        identifier = email or username
        if username and not email:
            try:
                looked_up = (
                    User.objects.filter(username__iexact=username).only("email").first()
                )
                if looked_up:
                    identifier = looked_up.email
            except Exception:  # noqa: BLE001
                # If the DB schema is behind and lacks `username`, fall back
                # to direct identifier auth.
                identifier = username
        user = authenticate(request, username=identifier, password=password)
        if user is None:
            return Response(
                {"detail": "Invalid username/email or password."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        return Response(TokenPairSerializer.for_user(user))


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        refresh = request.data.get("refresh")
        if refresh:
            try:
                token = RefreshToken(refresh)
                token.blacklist()
            except Exception as exc:  # noqa: BLE001
                logger.debug("Refresh blacklist skipped: %s", exc)
        return Response({"detail": "Logged out."})


class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)

    def patch(self, request):
        ser = UserSerializer(request.user, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(ser.data)


class PreferencesView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request):
        ser = PreferencesSerializer(
            request.user, data=request.data, partial=True
        )
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(UserSerializer(request.user).data)


class GoogleAuthView(APIView):
    """
    POST { "id_token": "<google id_token>" } or { "access_token": "..." }.

    Validates the token with Google, then signs the user in (or creates them
    on first sight) and returns the JWT pair.
    """

    permission_classes = [permissions.AllowAny]

    GOOGLE_TOKENINFO = "https://oauth2.googleapis.com/tokeninfo"
    GOOGLE_USERINFO = "https://www.googleapis.com/oauth2/v3/userinfo"

    def post(self, request):
        id_token = request.data.get("id_token")
        access_token = request.data.get("access_token")
        if not id_token and not access_token:
            return Response(
                {"detail": "id_token or access_token is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            profile = self._verify(id_token=id_token, access_token=access_token)
        except ValueError as exc:
            return Response(
                {"detail": str(exc)}, status=status.HTTP_401_UNAUTHORIZED
            )

        email = (profile.get("email") or "").strip().lower()
        if not email:
            return Response(
                {"detail": "Google account did not return an email."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "username": email,
                "full_name": profile.get("name") or "",
                "avatar_url": profile.get("picture") or "",
            },
        )
        if not created and not user.full_name and profile.get("name"):
            user.full_name = profile.get("name")
            user.avatar_url = profile.get("picture") or user.avatar_url
            user.save(update_fields=["full_name", "avatar_url", "updated_at"])

        if user.is_staff or user.is_superuser or getattr(user, "role", "") == "admin":
            return Response(
                {"detail": "Admin accounts must sign in with username and password."},
                status=status.HTTP_403_FORBIDDEN,
            )

        return Response(TokenPairSerializer.for_user(user))

    def _verify(self, *, id_token: str | None, access_token: str | None) -> dict:
        client_id = getattr(settings, "GOOGLE_OAUTH_CLIENT_ID", "") or ""
        if id_token:
            r = requests.get(
                self.GOOGLE_TOKENINFO,
                params={"id_token": id_token},
                timeout=10,
            )
            if r.status_code != 200:
                raise ValueError("Google id_token verification failed.")
            data = r.json()
            if client_id and data.get("aud") != client_id:
                raise ValueError("Google id_token audience mismatch.")
            return data
        # Access token path
        r = requests.get(
            self.GOOGLE_USERINFO,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        )
        if r.status_code != 200:
            raise ValueError("Google access_token verification failed.")
        return r.json()


class PasswordResetRequestView(APIView):
    """POST with email — always returns 200 for privacy."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        ser = PasswordResetRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        email = ser.validated_data["email"].strip().lower()
        user = User.objects.filter(email__iexact=email).first()
        if user and user.has_usable_password():
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            base = settings.FRONTEND_URL.rstrip("/")
            reset_url = f"{base}/reset-password?uid={uid}&token={token}"
            body = (
                "You asked to reset your LankaGuide password.\n\n"
                f"Open this link (valid 24h):\n{reset_url}\n\n"
                "If you did not request this, you can ignore this email."
            )
            try:
                send_mail(
                    subject="Reset your LankaGuide password",
                    message=body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=False,
                )
            except Exception as exc:
                logger.warning("password reset email failed: %s", exc)
        return Response(
            {
                "detail": "If an account exists for that email, "
                "we sent password reset instructions."
            }
        )


class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        ser = PasswordResetConfirmSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        uid_b64 = ser.validated_data["uid"]
        token = ser.validated_data["token"]
        password = ser.validated_data["new_password"]
        try:
            uid = force_str(urlsafe_base64_decode(uid_b64))
            user = User.objects.get(pk=uid)
        except (User.DoesNotExist, ValueError, TypeError):
            return Response(
                {"detail": "Invalid or expired reset link."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not default_token_generator.check_token(user, token):
            return Response(
                {"detail": "Invalid or expired reset link."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user.set_password(password)
        user.save(update_fields=["password"])
        return Response({"detail": "Your password has been updated. You can sign in now."})


class PasswordChangeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        ser = PasswordChangeSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = request.user
        if not user.check_password(ser.validated_data["old_password"]):
            return Response(
                {"detail": "Current password is incorrect."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user.set_password(ser.validated_data["new_password"])
        user.save(update_fields=["password"])
        return Response({"detail": "Password changed."})
