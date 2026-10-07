from django.core.management.base import BaseCommand, CommandError
from apps.portal.delivery import enqueue
from apps.portal.models import Digest, Subscriber


class Command(BaseCommand):
    help = 'Preview recipient count; --send freezes the audience and queues delivery for digest_worker.'

    def add_arguments(self, parser):
        parser.add_argument('digest_id', type=int)
        parser.add_argument('--send', action='store_true')

    def handle(self, *args, **options):
        try:
            digest = Digest.objects.get(pk=options['digest_id'])
        except Digest.DoesNotExist:
            raise CommandError('Digest not found')
        if not options['send']:
            count = (Subscriber.objects.filter(is_active=True).count() if digest.state == 'draft'
                     else digest.delivery_set.count())
            self.stdout.write(f'{count} recipients; no email sent. Use --send to queue delivery.')
            return
        try:
            digest = enqueue(digest.pk)
        except ValueError as exc:
            raise CommandError(str(exc))
        self.stdout.write(f'Digest {digest.pk}: {digest.state}. Run digest_worker to process the queue.')
