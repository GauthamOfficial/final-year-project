"""Admin dashboard endpoints (users, content, KPIs, ingestion controls)."""

from __future__ import annotations

import io
import logging
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db.models import Count, Q
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.attractions.models import Attraction, District, MediaAsset
from apps.chat.models import ChatMessage, ChatSession
from apps.itinerary.models import Itinerary
from apps.sentiment.models import Review

from .permissions import IsAdminRole
from .serializers import (
    AdminAttractionSerializer,
    AdminChatMessageSerializer,
    AdminChatSessionSerializer,
    AdminDistrictSerializer,
    AdminItinerarySerializer,
    AdminMediaSerializer,
    AdminReviewSerializer,
    AdminUserSerializer,
)

logger = logging.getLogger("lankaguide.admin_api")

User = get_user_model()


class KpiView(APIView):
    """High-level dashboard counters + recent activity feed."""

    permission_classes = [IsAdminRole]

    def get(self, request):
        now = timezone.now()
        day_ago = now - timedelta(days=1)
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)

        users_total = User.objects.count()
        users_active_24h = ChatSession.objects.filter(
            last_activity_at__gte=day_ago
        ).values("user_id").distinct().count()
        users_active_7d = ChatSession.objects.filter(
            last_activity_at__gte=week_ago
        ).values("user_id").distinct().count()
        users_new_30d = User.objects.filter(date_joined__gte=month_ago).count()

        attractions = Attraction.objects.count()
        districts = District.objects.count()
        media = MediaAsset.objects.count()
        itineraries = Itinerary.objects.count()
        chat_sessions = ChatSession.objects.count()
        chat_messages = ChatMessage.objects.count()
        reviews = Review.objects.count()

        top_attractions = list(
            Attraction.objects.order_by("-trend_score").values(
                "id", "name", "slug", "trend_score", "category"
            )[:8]
        )
        sentiment_breakdown = list(
            Review.objects.values("sentiment_label")
            .order_by()
            .annotate(count=Count("id"))
        )
        recent_chats = list(
            ChatSession.objects.select_related("user")
            .order_by("-last_activity_at")
            .values(
                "id",
                "title",
                "user__email",
                "language",
                "last_activity_at",
            )[:8]
        )
        recent_itineraries = list(
            Itinerary.objects.select_related("user")
            .order_by("-created_at")
            .values(
                "id",
                "title",
                "user__email",
                "start_date",
                "end_date",
                "created_at",
            )[:8]
        )

        return Response(
            {
                "users": {
                    "total": users_total,
                    "active_24h": users_active_24h,
                    "active_7d": users_active_7d,
                    "new_30d": users_new_30d,
                },
                "content": {
                    "districts": districts,
                    "attractions": attractions,
                    "media_assets": media,
                },
                "engagement": {
                    "itineraries": itineraries,
                    "chat_sessions": chat_sessions,
                    "chat_messages": chat_messages,
                    "reviews": reviews,
                },
                "top_attractions": top_attractions,
                "sentiment_breakdown": sentiment_breakdown,
                "recent_chats": recent_chats,
                "recent_itineraries": recent_itineraries,
                "generated_at": now.isoformat(),
            }
        )


class AdminUserViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminRole]
    serializer_class = AdminUserSerializer
    http_method_names = ["get", "patch", "head", "options"]

    def get_queryset(self):
        qs = User.objects.annotate(
            chat_session_count=Count("chat_sessions", distinct=True),
            itinerary_count=Count("itineraries", distinct=True),
        ).order_by("-date_joined")
        q = self.request.query_params.get("q")
        if q:
            qs = qs.filter(
                Q(email__icontains=q)
                | Q(full_name__icontains=q)
                | Q(home_country__icontains=q)
            )
        role = self.request.query_params.get("role")
        if role:
            qs = qs.filter(role=role)
        active = self.request.query_params.get("active")
        if active in {"true", "false"}:
            qs = qs.filter(is_active=(active == "true"))
        return qs

    @action(detail=True, methods=["post"], url_path="set-role")
    def set_role(self, request, pk=None):
        user = self.get_object()
        role = (request.data or {}).get("role")
        if role not in {"tourist", "editor", "admin"}:
            return Response(
                {"detail": "Invalid role."}, status=status.HTTP_400_BAD_REQUEST
            )
        user.role = role
        if role == "admin":
            user.is_staff = True
        else:
            user.is_staff = bool(request.data.get("is_staff", False))
        user.save(update_fields=["role", "is_staff"])
        return Response(self.get_serializer(user).data)

    @action(detail=True, methods=["post"], url_path="set-active")
    def set_active(self, request, pk=None):
        user = self.get_object()
        is_active = bool((request.data or {}).get("is_active", True))
        user.is_active = is_active
        user.save(update_fields=["is_active"])
        return Response(self.get_serializer(user).data)


class AdminDistrictViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminRole]
    serializer_class = AdminDistrictSerializer
    pagination_class = None

    def get_queryset(self):
        return District.objects.annotate(
            attraction_count=Count("attractions")
        ).order_by("name")


class AdminAttractionViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminRole]
    serializer_class = AdminAttractionSerializer

    def get_queryset(self):
        qs = Attraction.objects.annotate(
            media_count=Count("media")
        ).select_related("district").order_by("-trend_score", "name")
        district = self.request.query_params.get("district")
        if district and str(district).isdigit():
            qs = qs.filter(district_id=int(district))
        category = self.request.query_params.get("category")
        if category:
            qs = qs.filter(category=category)
        q = self.request.query_params.get("q")
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(slug__icontains=q))
        return qs


class AdminMediaPagination(PageNumberPagination):
    page_size = 80
    page_size_query_param = "page_size"
    max_page_size = 250


class AdminMediaViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminRole]
    serializer_class = AdminMediaSerializer
    pagination_class = AdminMediaPagination

    def get_queryset(self):
        qs = (
            MediaAsset.objects.select_related(
                "attraction",
                "attraction__district",
                "district",
            )
            .all()
            .order_by("-id")
        )
        attraction = self.request.query_params.get("attraction")
        if attraction and str(attraction).isdigit():
            qs = qs.filter(attraction_id=int(attraction))
        district = self.request.query_params.get("district")
        if district and str(district).isdigit():
            qs = qs.filter(
                Q(district_id=int(district))
                | Q(attraction__district_id=int(district))
            )
        return qs


class AdminItineraryViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAdminRole]
    serializer_class = AdminItinerarySerializer

    def get_queryset(self):
        return (
            Itinerary.objects.select_related("user")
            .annotate(day_count=Count("days"))
            .order_by("-created_at")
        )


class AdminChatViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAdminRole]
    serializer_class = AdminChatSessionSerializer

    def get_queryset(self):
        qs = (
            ChatSession.objects.select_related("user")
            .annotate(message_count=Count("messages"))
            .order_by("-last_activity_at")
        )
        user_id = self.request.query_params.get("user_id")
        if user_id and user_id.isdigit():
            qs = qs.filter(user_id=int(user_id))
        return qs

    @action(detail=True, methods=["get"], url_path="messages")
    def messages(self, request, pk=None):
        session = self.get_object()
        msgs = session.messages.order_by("created_at")
        return Response(
            AdminChatMessageSerializer(msgs, many=True).data
        )


class AdminReviewViewSet(viewsets.ReadOnlyModelViewSet):
    """Browse ingested reviews / sentiment rows for moderation."""

    permission_classes = [IsAdminRole]
    serializer_class = AdminReviewSerializer

    def get_queryset(self):
        qs = Review.objects.select_related("attraction").order_by("-ingested_at")
        label = self.request.query_params.get("sentiment_label")
        if label:
            qs = qs.filter(sentiment_label=label)
        q = self.request.query_params.get("q")
        if q:
            qs = qs.filter(
                Q(body__icontains=q) | Q(external_id__icontains=q)
            )
        return qs


class IngestKnowledgeView(APIView):
    """Trigger `manage.py ingest_knowledge_base` from the admin UI."""

    permission_classes = [IsAdminRole]

    def post(self, request):
        reset = bool((request.data or {}).get("reset", False))
        out = io.StringIO()
        try:
            call_command(
                "ingest_knowledge_base",
                stdout=out,
                stderr=out,
                reset=reset,
            )
        except Exception as exc:
            logger.exception("ingest_knowledge_base failed")
            return Response(
                {
                    "detail": str(exc),
                    "log": out.getvalue(),
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return Response(
            {
                "ok": True,
                "log": out.getvalue(),
                "reset": reset,
            }
        )


class CorpusStatsView(APIView):
    """Return chunk count + collection name for the dashboard."""

    permission_classes = [IsAdminRole]

    def get(self, request):
        try:
            from apps.core.services.vectorstore import get_collection
            from django.conf import settings as dj_settings

            col = get_collection(dj_settings.CHROMA_COLLECTION)
            count = col.count()
            return Response(
                {
                    "collection": dj_settings.CHROMA_COLLECTION,
                    "persist_dir": dj_settings.CHROMA_PERSIST_DIR,
                    "chunk_count": count,
                }
            )
        except Exception as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
