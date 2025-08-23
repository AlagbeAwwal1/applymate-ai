from django.contrib.auth.models import User
from rest_framework import serializers

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    class Meta:
        model = User
        fields = ["username","email","password"]
    def create(self, data):
        return User.objects.create_user(
            username=data["username"],
            email=data.get("email",""),
            password=data["password"]
        )
