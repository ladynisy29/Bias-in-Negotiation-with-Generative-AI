from django.conf import settings
from django.db import connection
from django.db.utils import DatabaseError
from django.core.validators import EmailValidator
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from users_api.auth import (
    create_access_token,
    get_authenticated_user,
    hash_user_password,
    revoke_access_token,
    verify_user_password,
)
from users_api.models import UserProfile


class CreateTestUserView(APIView):
    def post(self, request):
        if not (settings.DEBUG or getattr(settings, "ALLOW_DEV_AUTH_ENDPOINTS", False)):
            return Response({"error": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        payload = request.data or {}
        username = str(payload.get("username") or "test_user").strip()
        if not username:
            username = "test_user"

        suffix = UserProfile.objects.filter(username__startswith=username).count() + 1
        final_username = f"{username}_{suffix}"

        age_value = payload.get("age")
        parsed_age = None
        if age_value not in (None, ""):
            try:
                parsed_age = int(age_value)
            except (TypeError, ValueError):
                parsed_age = None

        user = UserProfile.objects.create(
            username=final_username,
            password_hash=hash_user_password("dev-password"),
            age=parsed_age,
            gender=str(payload.get("gender", "")).strip(),
            location=str(payload.get("location", "")).strip(),
            nationality=str(payload.get("nationality", "")).strip(),
            native_language=str(payload.get("native_language", "")).strip(),
            occupation=str(payload.get("occupation", "")).strip(),
            education_level=str(payload.get("education_level", "bachelor")),
            negotiation_experience=str(payload.get("negotiation_experience", "some")),
        )
        token, _ = create_access_token(user)

        return Response(
            {
                "user_id": str(user.user_id),
                "username": user.username,
                "access_token": token,
                "age": user.age,
                "gender": user.gender,
                "location": user.location,
                "nationality": user.nationality,
                "native_language": user.native_language,
                "occupation": user.occupation,
                "education_level": user.education_level,
                "negotiation_experience": user.negotiation_experience,
                "message": "Test user created.",
            },
            status=201,
        )


class HealthAuthPlaceholderView(APIView):
    def get(self, request):
        database_ok = True
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        except DatabaseError:
            database_ok = False

        payload = {
            "status": "ok" if database_ok else "degraded",
            "service": "bias-backend",
            "database": "ok" if database_ok else "unreachable",
        }
        http_status = status.HTTP_200_OK if database_ok else status.HTTP_503_SERVICE_UNAVAILABLE
        return Response(payload, status=http_status)


class UptimePingView(APIView):
    def get(self, request):
        return Response({"status": "ok", "message": "pong"}, status=status.HTTP_200_OK)


class SignupView(APIView):
    def post(self, request):
        payload = request.data or {}
        username = str(payload.get("username") or "").strip().lower()
        email = str(payload.get("email") or "").strip().lower()
        password = str(payload.get("password") or "")
        age_value = payload.get("age")
        parsed_age = None

        if age_value not in (None, ""):
            try:
                parsed_age = int(age_value)
            except (TypeError, ValueError):
                return Response(
                    {"error": "Age must be a valid number."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if parsed_age < 0:
                return Response(
                    {"error": "Age must be zero or greater."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        if not username or not password:
            return Response(
                {"error": "Username and password are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if len(password) < 8:
            return Response(
                {"error": "Password must be at least 8 characters."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if email:
            try:
                EmailValidator()(email)
            except DjangoValidationError:
                raise ValidationError({"email": "Invalid email format."})

        if UserProfile.objects.filter(username=username).exists():
            return Response(
                {"error": "User already exists"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = UserProfile.objects.create(
            username=username,
            password_hash=hash_user_password(password),
            age=parsed_age,
            gender=str(payload.get("gender") or "").strip(),
            location=str(payload.get("location") or "").strip(),
            nationality=str(payload.get("nationality") or "").strip(),
            native_language=str(payload.get("native_language") or "").strip(),
            occupation=str(payload.get("occupation") or "").strip(),
            education_level=str(payload.get("education_level") or "unknown").strip() or "unknown",
            negotiation_experience=str(payload.get("negotiation_experience") or "none").strip() or "none",
        )
        token, _ = create_access_token(user)

        return Response(
            {
                "message": "User created successfully",
                "user_id": str(user.user_id),
                "username": user.username,
                "access_token": token,
            },
            status=status.HTTP_201_CREATED
        )

class LoginView(APIView):

    def post(self, request):
        username = str(request.data.get("username") or "").strip().lower()
        password = str(request.data.get("password") or "")

        if not username or not password:
            return Response(
                {"error": "Username and password are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = UserProfile.objects.filter(username=username).first()

        if user is None or not verify_user_password(password, user.password_hash):
            return Response(
                {"error": "Invalid credentials"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        token, _ = create_access_token(user)

        return Response(
            {
                "message": "Login successful",
                "user_id": str(user.user_id),
                "access_token": token,
            },
            status=status.HTTP_200_OK
        )


class LogoutView(APIView):
    def post(self, request):
        get_authenticated_user(request)
        auth_header = request.headers.get("Authorization", "")
        raw_token = auth_header.removeprefix("Bearer ").strip()
        revoke_access_token(raw_token)
        return Response({"message": "Logged out."}, status=status.HTTP_200_OK)