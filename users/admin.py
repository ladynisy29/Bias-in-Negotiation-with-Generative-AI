from django.contrib import admin
from .models import UserProfile, NegotiationSession, DialogueTurn, OfferHistory

admin.site.register(UserProfile)
admin.site.register(NegotiationSession)
admin.site.register(DialogueTurn)
admin.site.register(OfferHistory)