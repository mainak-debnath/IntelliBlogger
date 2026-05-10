from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0003_blogpost_updated_at_and_constraints"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="BlogGenerationJob",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("youtube_link", models.URLField()),
                ("normalized_youtube_link", models.URLField()),
                ("tone", models.CharField(default="professional", max_length=50)),
                ("length", models.CharField(default="medium", max_length=20)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("queued", "Queued"),
                            ("processing", "Processing"),
                            ("completed", "Completed"),
                            ("failed", "Failed"),
                        ],
                        default="queued",
                        max_length=20,
                    ),
                ),
                ("title", models.CharField(blank=True, max_length=300)),
                ("generated_content", models.TextField(blank=True)),
                ("error_message", models.TextField(blank=True)),
                ("started_at", models.DateTimeField(blank=True, null=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.AddIndex(
            model_name="bloggenerationjob",
            index=models.Index(
                fields=["user", "-created_at"], name="job_user_created_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="bloggenerationjob",
            index=models.Index(
                fields=["status", "created_at"], name="job_status_created_idx"
            ),
        ),
    ]
