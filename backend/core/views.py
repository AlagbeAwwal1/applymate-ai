from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth.models import User
from .serializers import RegisterSerializer

@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    s = RegisterSerializer(data=request.data)
    s.is_valid(raise_exception=True)
    user = s.save()
    return Response({"id": user.id, "username": user.username, "email": user.email})

@api_view(["GET"])
def me(request):
    u: User = request.user
    return Response({"id": u.id, "username": u.username, "email": u.email})
