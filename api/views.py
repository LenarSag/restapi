import uuid

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.response import Response
from rest_framework import exceptions, status
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view, permission_classes

from .serializers import UserSerializer, UserUUIDSerializer
from .utils import generate_access_token, generate_refresh_token


User = get_user_model()


def get_user_from_serialized_refresh_token(request):
    serializer = UserUUIDSerializer(data=request.data)
    if serializer.is_valid():
        refresh_token_data = serializer.validated_data.get("refresh_token")
        user = User.objects.filter(refresh_token=refresh_token_data).first()
        if user is None:
            raise exceptions.ValidationError("Please provide the correct refresh token")
        return user
    else:
        raise exceptions.ValidationError(serializer.errors)


@api_view(["POST"])
@permission_classes([AllowAny])
def register_view(request):
    serializer = UserSerializer(data=request.data)
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

    return Response(
        data={
            "access_token": access_token,
            "refresh_token": refresh_token,
        }
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def logout_view(request):
    user = get_user_from_serialized_refresh_token(request)
    user.refresh_token_created_at = None
    user.refresh_token_expires_at = None
    user.save()
    return Response({"success": "User logged out."})


@api_view(["POST"])
@permission_classes([AllowAny])
def refresh_token(request):
    user = get_user_from_serialized_refresh_token(request)
    expire_time = user.refresh_token_expires_at
    if expire_time is None or expire_time < timezone.now():
        raise exceptions.AuthenticationFailed(
            "Expired refresh token, please login again."
        )

    access_token = generate_access_token(user)
    refresh_token = generate_refresh_token(user)

    return Response(
        data={
            "access_token": access_token,
            "refresh_token": refresh_token,
        },
        status=status.HTTP_201_CREATED,
    )
