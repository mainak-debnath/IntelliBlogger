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


class BlogGenerationJob(models.Model):
    class Status(models.TextChoices):
        QUEUED = "queued", "Queued"
        PROCESSING = "processing", "Processing"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    youtube_link = models.URLField()
    normalized_youtube_link = models.URLField()
    tone = models.CharField(max_length=50, default="professional")
    length = models.CharField(max_length=20, default="medium")
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.QUEUED
    )
    title = models.CharField(max_length=300, blank=True)
    generated_content = models.TextField(blank=True)
    error_message = models.TextField(blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "-created_at"], name="job_user_created_idx"),
            models.Index(fields=["status", "created_at"], name="job_status_created_idx"),
        ]

    def __str__(self):
        return f"Job {self.id} ({self.status})"
