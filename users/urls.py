from django.urls import path
from users.views import SignupView, LoginView, start_session, get_session, submit_final_offer
urlpatterns = [
    path("register/", SignupView, name="register"),
    path("login/", LoginView, name="login"),
    path('start-session/', start_session, name='start_session'),
    path('session/<int:session_id>/', get_session, name='get_session'),
    path('session/<int:session_id>/submit-final-offer/', submit_final_offer, name='submit')
    ]