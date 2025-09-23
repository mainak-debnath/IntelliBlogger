from __future__ import annotations

from typing import Optional

from django.contrib.auth.models import User
from django.db.models import QuerySet

from api.models import BlogPost


class BlogRepository:
    def create(
        self,
        *,
        user: User,
        youtube_title: str,
        youtube_link: str,
        generated_content: str,
    ) -> BlogPost:
        post = BlogPost.objects.create(
            user=user,
            youtube_title=youtube_title,
            youtube_link=youtube_link,
            generated_content=generated_content,
        )
        return post

    def list_for_user(
        self, user: User, query: Optional[str] = None
    ) -> QuerySet[BlogPost]:
        qs = BlogPost.objects.filter(user=user)
        if query:
            qs = qs.filter(youtube_title__icontains=query)
        return qs.order_by("-id")

    def get(self, *, pk: int) -> BlogPost:
        return BlogPost.objects.get(id=pk)

    def delete(self, *, post: BlogPost) -> None:
        post.delete()
