import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models


class MyUser(AbstractUser):
    refresh_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    refresh_token_created_at = models.DateTimeField(null=True, blank=True)
    refresh_token_expires_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.username
