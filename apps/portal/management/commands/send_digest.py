from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.urls import reverse
from django.utils import timezone
from django.utils.html import escape, strip_tags

from apps.portal.models import Delivery, Digest, Subscriber


class Command(BaseCommand):
    help = 'Preview a digest delivery count. Use --send after configuring SMTP to send it.'

    def add_arguments(self, parser):
        parser.add_argument('digest_id', type=int)
        parser.add_argument('--send', action='store_true')

    def handle(self, *args, **options):
        try:
            digest = Digest.objects.get(pk=options['digest_id'])
        except Digest.DoesNotExist:
            raise CommandError('Digest not found')
        subscribers = Subscriber.objects.filter(is_active=True).exclude(delivery__digest=digest)
        if not options['send']:
            self.stdout.write('{} recipients; no email sent. Use --send to deliver.'.format(subscribers.count()))
            return
        if settings.EMAIL_BACKEND != 'django.core.mail.backends.smtp.EmailBackend':
            raise CommandError('Configure the SMTP email backend before sending.')
        error = None
        sent = 0
        # Lock the issue so two workers cannot send the same issue concurrently.
        # Commit completed deliveries even when a later recipient fails.
        with transaction.atomic():
            digest = Digest.objects.select_for_update().get(pk=digest.pk)
            for subscriber in subscribers:
                unsubscribe = settings.SITE_URL.rstrip('/') + reverse('unsubscribe', args=[subscriber.token])
                html = digest.body + '<p><a href="{}">Отписаться от дайджеста</a></p>'.format(escape(unsubscribe))
                email = EmailMultiAlternatives(digest.subject, strip_tags(digest.body) + '\n\nОтписаться: ' + unsubscribe,
                                               settings.DEFAULT_FROM_EMAIL, [subscriber.email])
                email.attach_alternative(html, 'text/html')
                try:
                    if not email.send():
                        raise RuntimeError('Mail backend accepted no message')
                except Exception as exc:
                    error = str(exc)
                    break
                Delivery.objects.create(digest=digest, subscriber=subscriber)
                sent += 1
            if error is None:
                digest.sent_at = timezone.now()
                digest.save(update_fields=['sent_at'])
        self.stdout.write('{} messages sent.'.format(sent))
        if error:
            raise CommandError('Delivery stopped; retry skips recorded deliveries: {}'.format(error))
