import uuid

from django.db import models


class UserProfile(models.Model):
    user_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=50, unique=True)
    password_hash = models.CharField(max_length=255)
    age = models.PositiveIntegerField()
    gender = models.CharField(max_length=30)
    education_level = models.CharField(max_length=30)
    negotiation_experience = models.CharField(max_length=30)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.username


class NegotiationSession(models.Model):
    OUTCOME_CHOICES = [
        ("Accepted", "Accepted"),
        ("Declined", "Declined"),
        ("Abandoned", "Abandoned"),
    ]

    session_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name="sessions")
    ai_reservation_price = models.FloatField()
    initial_offer = models.FloatField()
    final_offer = models.FloatField(null=True, blank=True)
    final_price = models.FloatField(null=True, blank=True)
    outcome = models.CharField(max_length=20, choices=OUTCOME_CHOICES, null=True, blank=True)
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
    extracted_offer = models.FloatField(null=True, blank=True)
    reasoning = models.TextField(null=True, blank=True)
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
