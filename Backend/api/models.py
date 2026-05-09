from django.contrib.auth.models import User
from django.db import models


class BlogPost(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    youtube_title = models.CharField(max_length=300)
    youtube_link = models.URLField()
    generated_content = models.TextField()
    tone = models.CharField(max_length=50, default="professional")
    length = models.CharField(max_length=20, default="medium")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "youtube_link", "tone", "length"],
                name="unique_blog_per_user_link_tone_length",
            )
        ]
        indexes = [
            models.Index(fields=["user", "-created_at"], name="blog_user_created_idx"),
        ]

    def __str__(self):
        return f"{self.youtube_title} ({self.tone}, {self.length})"
