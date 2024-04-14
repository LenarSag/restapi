import uuid

import jwt
from django.conf import settings
from django.utils import timezone


def generate_access_token(user):
    access_token_payload = {
        "user_id": user.id,
        "exp": timezone.now() + settings.ACCESS_TOKEN_LIFETIME,
        "iat": timezone.now(),
    }
    access_token = jwt.encode(
        access_token_payload, settings.JWT_SECRET_KEY, algorithm="HS256"
    )
    return access_token


def generate_refresh_token(user):
    user.refresh_token = uuid.uuid4()
    user.refresh_token_created_at = timezone.now()
    user.refresh_token_expires_at = timezone.now() + settings.REFRESH_TOKEN_LIFETIME
    user.save()
    return user.refresh_token
