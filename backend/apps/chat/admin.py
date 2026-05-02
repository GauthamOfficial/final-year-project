from django.contrib import admin

from .models import ChatMessage, ChatSession


class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    readonly_fields = ("role", "content", "retrieved_docs", "tokens_used", "backend", "created_at")


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "title", "language", "started_at", "last_activity_at")
    list_filter = ("language",)
    search_fields = ("user__email", "title")
    inlines = [ChatMessageInline]


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "session", "role", "tokens_used", "backend", "created_at")
    list_filter = ("role", "backend")
    search_fields = ("content",)
