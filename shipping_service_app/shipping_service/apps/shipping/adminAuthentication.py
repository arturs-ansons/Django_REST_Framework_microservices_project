from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework import exceptions
from django.contrib.auth import get_user_model

User = get_user_model()

class AdminJWTAuthentication(JWTAuthentication):
    """Authenticate admin using real Django user from JWT."""

    def get_user(self, validated_token):
        user_id = validated_token.get("user_id")

        if not user_id:
            raise exceptions.AuthenticationFailed(
                "Token has no user_id", code="user_id_missing"
            )

        # Cast user_id to int to match DB
        try:
            user_id = int(user_id)
        except (TypeError, ValueError):
            raise exceptions.AuthenticationFailed(
                "Invalid user_id type", code="invalid_user_id"
            )

        try:
            user = User.objects.get(id=int(user_id))
        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed("User not found", code="user_not_found")

        return user
