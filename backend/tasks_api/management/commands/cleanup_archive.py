from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from tasks_api.models import Task


class Command(BaseCommand):
    help = "Permanently delete tasks archived more than 30 days ago."

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=30)

    def handle(self, *args, **options):
        cutoff = timezone.now() - timedelta(days=options["days"])
        deleted, _ = Task.objects.filter(archived_at__lt=cutoff).delete()
        self.stdout.write(f"Deleted {deleted} archived task(s) older than {options['days']} days.")
