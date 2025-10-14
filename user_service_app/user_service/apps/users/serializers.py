from rest_framework import serializers
from .models import CustomUser

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = CustomUser
        fields = ("id", "username", "email", "phone_number", "password")

    def create(self, validated_data):
        user = CustomUser.objects.create_user(
            username=validated_data["username"],
            email=validated_data.get("email"),
            phone_number=validated_data.get("phone_number"),
            password=validated_data["password"],
        )
        return user
    
    
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Adds is_admin and username claims to the JWT token.
    """

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        token["is_admin"] = user.is_staff
        token["username"] = user.username

        return token
