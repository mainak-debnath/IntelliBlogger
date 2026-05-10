from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0002_blogpost_length_blogpost_tone_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="blogpost",
            name="updated_at",
            field=models.DateTimeField(auto_now=True, default="2026-01-01T00:00:00Z"),
            preserve_default=False,
        ),
        migrations.AlterUniqueTogether(
            name="blogpost",
            unique_together=set(),
        ),
        migrations.AddConstraint(
            model_name="blogpost",
            constraint=models.UniqueConstraint(
                fields=("user", "youtube_link", "tone", "length"),
                name="unique_blog_per_user_link_tone_length",
            ),
        ),
        migrations.AddIndex(
            model_name="blogpost",
            index=models.Index(
                fields=["user", "-created_at"], name="blog_user_created_idx"
            ),
        ),
    ]
