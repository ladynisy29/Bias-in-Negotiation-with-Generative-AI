from django.urls import path

from users_api.views.api_views import DialogueHistoryView, SendMessageView
from users_api.views.auth_views import (
    CreateTestUserView,
    HealthAuthPlaceholderView,
    LoginView,
    LogoutView,
    SignupView,
)
from users_api.views.export_views import (
    ExportProfitAnalysisView,
    ExportSessionsCsvView,
    ExportTranscriptView,
)
from users_api.views.session_views import (
    AbandonSessionView,
    SessionDetailView,
    StartSessionView,
    SubmitFinalOfferView,
)

urlpatterns = [
    path("auth/health", HealthAuthPlaceholderView.as_view(), name="auth-health"),
    path("auth/dev-create-user", CreateTestUserView.as_view(), name="auth-dev-create-user"),
    path("auth/register", SignupView.as_view(), name="auth-register"),
    path("auth/login", LoginView.as_view(), name="auth-login"),
    path("auth/logout", LogoutView.as_view(), name="auth-logout"),
    path("start-session", StartSessionView.as_view(), name="start-session"),
    path("session/<uuid:session_id>", SessionDetailView.as_view(), name="session-detail"),
    path("session/<uuid:session_id>/abandon", AbandonSessionView.as_view(), name="session-abandon"),
    path("session/<uuid:session_id>/send-message", SendMessageView.as_view(), name="send-message"),
    path("session/<uuid:session_id>/dialogue", DialogueHistoryView.as_view(), name="dialogue-history"),
    path("session/<uuid:session_id>/submit-final-offer", SubmitFinalOfferView.as_view(), name="submit-final-offer"),
    path("export/sessions", ExportSessionsCsvView.as_view(), name="export-sessions"),
    path("export/session/<uuid:session_id>/transcript", ExportTranscriptView.as_view(), name="export-transcript"),
    path("export/profit-analysis", ExportProfitAnalysisView.as_view(), name="export-profit-analysis"),
]
