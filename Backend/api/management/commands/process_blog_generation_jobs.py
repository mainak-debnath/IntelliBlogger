from django.core.management.base import BaseCommand

from api.repositories.blog_repo import BlogGenerationJobRepository
from api.services.job_processing import BlogGenerationJobProcessor


class Command(BaseCommand):
    help = "Process queued blog generation jobs."

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=10,
            help="Maximum number of queued jobs to process.",
        )

    def handle(self, *args, **options):
        limit = options["limit"]
        repo = BlogGenerationJobRepository()
        processor = BlogGenerationJobProcessor()
        jobs = list(repo.list_queued(limit=limit))

        if not jobs:
            self.stdout.write(self.style.WARNING("No queued jobs found."))
            return

        for job in jobs:
            processor.process(job)
            self.stdout.write(f"Processed job {job.id} -> {job.status}")
