from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.serializers import RegisterSerializer, UserSerializer


class RegisterView(APIView):
    """Регистрация нового пользователя."""

    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    def post(self, request: Request) -> Response:
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return Response(
            {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
            },
            status=status.HTTP_201_CREATED,
        )


class MeView(APIView):
    """Получение данных текущего пользователя."""

    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get(self, request: Request) -> Response:
        serializer = self.serializer_class(request.user)
        return Response(serializer.data)
