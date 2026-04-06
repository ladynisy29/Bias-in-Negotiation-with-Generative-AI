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
