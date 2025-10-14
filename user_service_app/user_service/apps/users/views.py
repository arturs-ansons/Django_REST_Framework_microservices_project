from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .serializers import UserRegisterSerializer, CustomTokenObtainPairSerializer
from .models import CustomUser

# -------------------------------
# User Registration
# -------------------------------
class UserRegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            # return
            response_data = {
                "id": user.id,
                "username": user.username,
                "email": user.email,
            }
            return Response(response_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# -------------------------------
# User Login (JWT token)
# -------------------------------
class UserLoginView(TokenObtainPairView):
    """
    Returns JWT access and refresh tokens.
    Frontend and other microservices (like order_service) will use these tokens.
    """
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [AllowAny]


# -------------------------------
# Get User Details
# -------------------------------
class UserDetailView(APIView):
    permission_classes = [IsAuthenticated]  # Require JWT token

    def get(self, request, user_id):
        try:
            user = CustomUser.objects.get(id=user_id)
            # return safe user data only
            serializer = UserRegisterSerializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except CustomUser.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
