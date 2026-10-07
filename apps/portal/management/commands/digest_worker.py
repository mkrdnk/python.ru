import os
import socket
import time

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.portal.delivery import heartbeat, process_one, recover_stale


class Command(BaseCommand):
    help = 'Process queued digest deliveries. Use --once to drain the current queue and exit.'

    def add_arguments(self, parser):
        parser.add_argument('--once', action='store_true')

    def handle(self, *args, **options):
        if settings.EMAIL_BACKEND != 'django.core.mail.backends.smtp.EmailBackend':
            raise CommandError('Configure the SMTP email backend before starting the worker.')
        name = f'{socket.gethostname()}:{os.getpid()}'
        while True:
            heartbeat(name)
            recover_stale()
            processed = process_one()
            if not processed:
                if options['once']:
                    return
                time.sleep(5)
