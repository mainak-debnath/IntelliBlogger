from celery import shared_task

from api.models import BlogGenerationJob
from api.services.job_processing import BlogGenerationJobProcessor


@shared_task(name="api.process_blog_generation_job")
def process_blog_generation_job(job_id: int) -> dict:
    job = BlogGenerationJob.objects.get(id=job_id)
    updated_job = BlogGenerationJobProcessor().process(job)
    return {"job_id": updated_job.id, "status": updated_job.status}
