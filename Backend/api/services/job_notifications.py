from __future__ import annotations

import json

import redis
from django.conf import settings

from api.serializers import BlogGenerationJobSerializer


class BlogGenerationJobNotifier:
    def __init__(self):
        self.redis_url = settings.JOB_EVENT_STREAM_URL

    def get_pubsub(self, user_id: int):
        client = redis.Redis.from_url(self.redis_url, decode_responses=True)
        pubsub = client.pubsub()
        pubsub.subscribe(f"user_jobs_{user_id}")
        return pubsub

    def notify(self, job) -> None:
        client = redis.Redis.from_url(self.redis_url, decode_responses=True)
        payload = BlogGenerationJobSerializer(job).data
        client.publish(
            f"user_jobs_{job.user_id}",
            json.dumps(payload),
        )
