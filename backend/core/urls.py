from django.contrib import admin
from django.urls import include
from django.urls import path
import users.views.auth_views

from backend.users_api.views.auth_views import HealthAuthPlaceholderView, SignupView, LoginView

urlpatterns = {
    path("admin/", admin.site.urls),
    path("api/", include("users_api.urls")),
    path('api/auth/test/', HealthAuthPlaceholderView.as_view()),
    path('api/signup/', SignupView.as_view()),
    path('api/login/', LoginView.as_view()),
}
