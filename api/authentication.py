import jwt
from rest_framework.authentication import BaseAuthentication
from rest_framework import exceptions
from django.conf import settings
from django.contrib.auth import get_user_model


User = get_user_model()


class JWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        authorization_header = request.headers.get("Authorization")
        if not authorization_header:
            return None

        try:
            access_token = authorization_header.split(" ")[1]
            access_token_payload = jwt.decode(
                access_token, settings.JWT_SECRET_KEY, algorithms=["HS256"]
            )
        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed("Access token expired")
        except IndexError:
            raise exceptions.AuthenticationFailed("Token prefix missing")

        user = User.objects.filter(id=access_token_payload.get("user_id")).first()
        if user is None:
            raise exceptions.AuthenticationFailed("User not found")
        if not user.is_active:
            raise exceptions.AuthenticationFailed("User is inactive")

        return (user, None)
