from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # demographics
    age = models.IntegerField(null=True, blank=True)
    gender = models.CharField(max_length=20, null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    education = models.CharField(max_length=100, null=True, blank=True)
    occupation = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return self.user.username

class NegotiationSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    # basic info
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    # negotiation data
    scenario = models.TextField()
    strategy = models.CharField(max_length=100)

    # results
    outcome = models.TextField(blank=True, null=True)
    score = models.IntegerField(default=0)

    # timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
