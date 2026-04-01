from django.urls import path
from . import views

urlpatterns = [
    path('start-session/', views.start_session, name='start_session'),
    path('session/<int:session_id>/', views.get_session, name='get_session'),
    path('session/<int:session_id>/submit-final-offer/', views.submit_final_offer, name='submit_final_offer'),
]