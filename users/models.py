from django.db import models
from django.contrib.auth.models import User


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
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    scenario = models.TextField()
    strategy = models.CharField(max_length=100)

    outcome = models.TextField(blank=True, null=True)
    score = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class DialogueTurn(models.Model):
    session = models.ForeignKey(NegotiationSession, on_delete=models.CASCADE, related_name='turns')

    speaker = models.CharField(max_length=20)
    message = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.speaker}: {self.message[:30]}"


