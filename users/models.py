from django.db import models
from django.contrib.auth.models import User
import random
import uuid

class UserSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def generate_token(self):
        self.token = uuid.uuid4().hex

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    age = models.IntegerField(null=True, blank=True)
    gender = models.CharField(max_length=20, null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    education = models.CharField(max_length=100, null=True, blank=True)
    occupation = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return self.user.username


class NegotiationSession(models.Model):

    STATUS_ACTIVE = 'active'
    STATUS_COMPLETED = 'completed'
    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Active'),
        (STATUS_COMPLETED, 'Completed'),
    ]

    OUTCOME_ACCEPTED = 'accepted'
    OUTCOME_DECLINED = 'declined'
    OUTCOME_CHOICES = [
        (OUTCOME_ACCEPTED, 'Accepted'),
        (OUTCOME_DECLINED, 'Declined'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ai_reservation_price = models.FloatField(default=0)
    turn_count = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    outcome = models.CharField(max_length=20, choices=OUTCOME_CHOICES, null=True, blank=True)
    final_price = models.FloatField(null=True, blank=True)
    human_profit = models.FloatField(null=True, blank=True)
    ai_profit = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.pk and self.ai_reservation_price == 0:
            self.ai_reservation_price = random.uniform(850_000, 1_150_000)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Session #{self.pk} - {self.user.username} - {self.status}"

    class Meta:
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]

class DialogueTurn(models.Model):
    session = models.ForeignKey(NegotiationSession, on_delete=models.CASCADE, related_name='turns')
    speaker = models.CharField(max_length=20)
    message = models.TextField()
    turn_number = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Turn {self.turn_number} - {self.speaker}: {self.message[:30]}"

    class Meta:
        indexes = [
            models.Index(fields=['session']),
            models.Index(fields=['turn_number']),
        ]

class OfferHistory(models.Model):
    session = models.ForeignKey(NegotiationSession, on_delete=models.CASCADE, related_name='offers')
    offer_value = models.FloatField()
    sender = models.CharField(max_length=20)
    turn_number = models.IntegerField(default=0)
    concession_amount = models.FloatField(null=True, blank=True)
    concession_percentage = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return f"{self.sender}: {self.offer_value} (turn {self.turn_number})"

    class Meta:
        indexes = [
            models.Index(fields=['session']),
            models.Index(fields=['turn_number']),
        ]
