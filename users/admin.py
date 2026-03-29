from django.contrib import admin
from .models import UserProfile, NegotiationSession

admin.site.register(UserProfile)
admin.site.register(NegotiationSession)
