from datetime import timedelta
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from apps.portal.models import DigestWorker


class Command(BaseCommand):
    help = 'Fail unless a digest worker has checked in during the last two minutes.'

    def handle(self, *args, **options):
        if not DigestWorker.objects.filter(heartbeat__gte=timezone.now() - timedelta(minutes=2)).exists():
            raise CommandError('No active digest worker')
        self.stdout.write('Digest worker is active')
