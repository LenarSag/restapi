import uuid

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.response import Response
from rest_framework import exceptions, status
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view, permission_classes

from .serializers import UserSerializer
from .utils import generate_access_token, generate_refresh_token


User = get_user_model()


def get_user_from_refresh_token(request):
    refresh_token = request.data.get("refresh_token")
    if refresh_token is None:
        raise exceptions.PermissionDenied(
            "Credentials for refresh token were not provided."
        )
    try:
        uuid.UUID(refresh_token)
    except ValueError:
        raise exceptions.ValidationError("Invalid refresh token format")

    user = User.objects.filter(refresh_token=refresh_token).first()
    if user is None:
        raise exceptions.NotFound("Please provide the correct refresh token")
    return user


@api_view(["POST"])
@permission_classes([AllowAny])
def register_view(request):
    data = request.data
    serializer = UserSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET", "POST"])
def profile_view(request):
    user = request.user

    if request.method == "GET":
        serializer = UserSerializer(user)
        return Response(serializer.data)

    elif request.method == "POST":
        serializer = UserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request):
    username = request.data.get("username")
    password = request.data.get("password")
    response = Response()
    if (username is None) or (password is None):
        raise exceptions.AuthenticationFailed("Please enter username and password")

    user = User.objects.filter(username=username).first()
    if user is None:
        raise exceptions.AuthenticationFailed(
            "Please enter the correct username and password!"
        )
    if not user.check_password(password):
        raise exceptions.AuthenticationFailed(
            "Please enter the correct username and password!"
        )

    access_token = generate_access_token(user)
    refresh_token = generate_refresh_token(user)

    response.data = {
        "access_token": access_token,
        "refresh_token": refresh_token,
    }
    return response


@api_view(["POST"])
@permission_classes([AllowAny])
def logout_view(request):
    response = Response()
    user = get_user_from_refresh_token(request)
    user.refresh_token_created_at = None
    user.refresh_token_expires_at = None
    user.save()

    response.data = {"success": "User logged out."}
    return response


@api_view(["POST"])
@permission_classes([AllowAny])
def refresh_token(request):
    response = Response()
    user = get_user_from_refresh_token(request)
    expire_time = user.refresh_token_expires_at
    if expire_time is None or expire_time < timezone.now():
        raise exceptions.AuthenticationFailed(
            "Expired refresh token, please login again."
        )

    access_token = generate_access_token(user)
    refresh_token = generate_refresh_token(user)

    response.data = {
        "access_token": access_token,
        "refresh_token": refresh_token,
    }
    return response
