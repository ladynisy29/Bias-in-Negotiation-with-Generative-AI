from django.contrib import admin

from users_api.models import (
    DialogueTurn,
    NegotiationSession,
    OfferHistory,
    UserProfile,
    UserSessionToken,
)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("username", "age", "gender", "location", "nationality", "created_at")
    search_fields = ("username", "location", "nationality")


@admin.register(UserSessionToken)
class UserSessionTokenAdmin(admin.ModelAdmin):
    list_display = ("token_id", "user", "expires_at", "revoked_at", "last_used_at")
    search_fields = ("user__username", "token_prefix")
    list_filter = ("revoked_at",)


@admin.register(NegotiationSession)
class NegotiationSessionAdmin(admin.ModelAdmin):
    list_display = (
        "session_id",
        "user",
        "turn_count",
        "outcome",
        "session_status",
        "started_at",
        "ended_at",
    )
    search_fields = ("user__username",)
    list_filter = ("outcome", "session_status", "dropoff_stage")


@admin.register(DialogueTurn)
class DialogueTurnAdmin(admin.ModelAdmin):
    list_display = ("turn_id", "session", "turn_number", "speaker", "offer_amount", "timestamp")
    search_fields = ("session__user__username", "message")
    list_filter = ("speaker", "offer_made", "is_counter_offer", "sentiment", "strategy_tag")


@admin.register(OfferHistory)
class OfferHistoryAdmin(admin.ModelAdmin):
    list_display = ("offer_id", "session", "turn_number", "speaker", "offer_amount", "created_at")
    search_fields = ("session__user__username",)
    list_filter = ("speaker",)
