import uuid

from django.db import models
from django.utils import timezone


class UserProfile(models.Model):
    user_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=50, unique=True)
    password_hash = models.CharField(max_length=255)
    age = models.PositiveIntegerField(null=True, blank=True)
    gender = models.CharField(max_length=30, blank=True, default="")
    location = models.CharField(max_length=100, blank=True, default="")
    nationality = models.CharField(max_length=100, blank=True, default="")
    education_level = models.CharField(max_length=30)
    negotiation_experience = models.CharField(max_length=30)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.username


class UserSessionToken(models.Model):
    token_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name="session_tokens")
    token_prefix = models.CharField(max_length=16, db_index=True)
    token_hash = models.CharField(max_length=64, unique=True, db_index=True)
    expires_at = models.DateTimeField()
    last_used_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["user", "expires_at"])]

    @property
    def is_active(self) -> bool:
        return self.revoked_at is None and self.expires_at > timezone.now()


class NegotiationSession(models.Model):
    OUTCOME_CHOICES = [
        ("Accepted", "Accepted"),
        ("Declined", "Declined"),
        ("Abandoned", "Abandoned"),
    ]
    STATUS_CHOICES = [
        ("in_progress", "in_progress"),
        ("completed", "completed"),
        ("abandoned", "abandoned"),
        ("timeout", "timeout"),
    ]
    DROPOFF_STAGE_CHOICES = [
        ("before_offer", "before_offer"),
        ("mid_negotiation", "mid_negotiation"),
        ("after_offer", "after_offer"),
    ]

    session_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name="sessions")
    ai_reservation_price = models.FloatField()
    initial_offer = models.FloatField()
    final_offer = models.FloatField(null=True, blank=True)
    final_price = models.FloatField(null=True, blank=True)
    outcome = models.CharField(max_length=20, choices=OUTCOME_CHOICES, null=True, blank=True)
    session_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="in_progress")
    dropoff_stage = models.CharField(max_length=20, choices=DROPOFF_STAGE_CHOICES, null=True, blank=True)
    human_profit = models.FloatField(default=0)
    ai_profit = models.FloatField(default=0)
    turn_count = models.PositiveSmallIntegerField(default=0)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Session {self.session_id}"


class DialogueTurn(models.Model):
    SPEAKER_CHOICES = [("Human", "Human"), ("AI", "AI")]

    turn_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(NegotiationSession, on_delete=models.CASCADE, related_name="dialogue_turns")
    turn_number = models.PositiveSmallIntegerField()
    speaker = models.CharField(max_length=10, choices=SPEAKER_CHOICES)
    message = models.TextField(max_length=2000)
    offer_made = models.BooleanField(default=False)
    is_counter_offer = models.BooleanField(default=False)
    offer_amount = models.FloatField(null=True, blank=True)
    concession_amount = models.FloatField(null=True, blank=True)
    response_time_seconds = models.FloatField(null=True, blank=True)
    message_length = models.PositiveIntegerField(default=0)
    sentiment = models.CharField(max_length=10, blank=True, default="neutral")
    strategy_tag = models.CharField(max_length=20, blank=True, default="neutral")
    extracted_offer = models.FloatField(null=True, blank=True)
    reasoning = models.TextField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["turn_number", "created_at"]


class OfferHistory(models.Model):
    SPEAKER_CHOICES = [("Human", "Human"), ("AI", "AI")]

    offer_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(NegotiationSession, on_delete=models.CASCADE, related_name="offer_history")
    turn_number = models.PositiveSmallIntegerField()
    offer_amount = models.FloatField()
    speaker = models.CharField(max_length=10, choices=SPEAKER_CHOICES)
    concession_amount = models.FloatField(null=True, blank=True)
    concession_percentage = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["turn_number", "created_at"]
        indexes = [models.Index(fields=["session", "turn_number"])]
