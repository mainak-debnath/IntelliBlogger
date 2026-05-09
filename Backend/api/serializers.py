# api/serializers.py
from django.contrib.auth.models import User
from rest_framework import serializers

from api.models import BlogPost


class SignupSerializer(serializers.ModelSerializer):
    repeat_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ("username", "email", "password", "repeat_password")
        extra_kwargs = {"password": {"write_only": True, "min_length": 6}}

    def validate(self, data):
        if data.get("password") != data.get("repeat_password"):
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return data

    def create(self, validated_data):
        validated_data.pop("repeat_password", None)
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data.get("email", ""),
            password=validated_data["password"],
        )
        return user


class GenerateBlogRequestSerializer(serializers.Serializer):
    ALLOWED_TONES = ("professional", "casual", "witty", "technical")
    ALLOWED_LENGTHS = ("short", "medium", "long")

    link = serializers.URLField()
    tone = serializers.ChoiceField(choices=ALLOWED_TONES, default="professional")
    length = serializers.ChoiceField(choices=ALLOWED_LENGTHS, default="medium")


class SaveBlogRequestSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=300)
    content = serializers.CharField()
    link = serializers.URLField()
    tone = serializers.ChoiceField(
        choices=GenerateBlogRequestSerializer.ALLOWED_TONES, default="professional"
    )
    length = serializers.ChoiceField(
        choices=GenerateBlogRequestSerializer.ALLOWED_LENGTHS, default="medium"
    )
    force_update = serializers.BooleanField(default=False)


class BlogPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlogPost
        fields = [
            "id",
            "youtube_title",
            "youtube_link",
            "generated_content",
            "tone",
            "length",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "tone",
            "length",
            "youtube_link",
            "created_at",
            "updated_at",
        ]
