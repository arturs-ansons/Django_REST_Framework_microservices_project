# apps/shipping/authentication.py
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework import exceptions
from types import SimpleNamespace

class ServiceJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        user_id = validated_token.get("user_id")
        if not user_id:
            raise exceptions.AuthenticationFailed("Token has no user_id", code="user_id_missing")
        
        # Read admin info from token
        is_admin = validated_token.get("is_admin", False)
        
        return SimpleNamespace(
            id=user_id,
            is_authenticated=True,
            is_admin=is_admin
        )
