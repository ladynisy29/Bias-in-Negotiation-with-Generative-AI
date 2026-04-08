from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.validators import validate_email
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from users_api.models import UserProfile


class CreateTestUserView(APIView):
    def post(self, request):
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
            password_hash="dev-hash",
            age=parsed_age,
            gender=str(payload.get("gender", "")).strip(),
            location=str(payload.get("location", "")).strip(),
            nationality=str(payload.get("nationality", "")).strip(),
            education_level=str(payload.get("education_level", "bachelor")),
            negotiation_experience=str(payload.get("negotiation_experience", "some")),
        )

        return Response(
            {
                "user_id": str(user.user_id),
                "username": user.username,
                "age": user.age,
                "gender": user.gender,
                "location": user.location,
                "nationality": user.nationality,
                "message": "Test user created.",
            },
            status=201,
        )


class HealthAuthPlaceholderView(APIView):
    def get(self, request):
        return Response({"status": "auth module placeholder"})


class SignupView(APIView):

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return Response(
                {"error": "Email and password are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not validate_email(email):
            return Response(
                {"error": "Invalid email format"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not validate_password(password):
            return Response(
                {"error": "Password must be at least 6 characters"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if User.objects.filter(username=email).exists():
            return Response(
                {"error": "User already exists"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password
        )

        return Response(
            {
                "message": "User created successfully",
                "user_id": user.id
            },
            status=status.HTTP_201_CREATED
        )

class LoginView(APIView):

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return Response(
                {"error": "Email and password are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(username=email, password=password)

        if user is None:
            return Response(
                {"error": "Invalid credentials"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        return Response(
            {
                "message": "Login successful",
                "user_id": user.id
            },
            status=status.HTTP_200_OK
        )