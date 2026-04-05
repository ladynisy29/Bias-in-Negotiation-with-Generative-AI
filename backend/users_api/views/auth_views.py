from rest_framework.response import Response
from rest_framework.views import APIView


class HealthAuthPlaceholderView(APIView):
    def get(self, request):
        return Response({"status": "auth module placeholder"})
