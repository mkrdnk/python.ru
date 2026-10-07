"""Database-backed digest queue. SMTP outcomes are never retried implicitly."""
import smtplib
import uuid
from datetime import timedelta

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.urls import reverse
from django.utils import timezone
from django.utils.html import escape, strip_tags

from apps.portal.models import Delivery, Digest, DigestWorker, Subscriber

STALE_AFTER = timedelta(minutes=5)


def enqueue(digest_id):
    if settings.EMAIL_BACKEND != 'django.core.mail.backends.smtp.EmailBackend':
        raise ValueError('Настройте SMTP перед отправкой.')
    with transaction.atomic():
        digest = Digest.objects.select_for_update().get(pk=digest_id)
        if digest.state != 'draft':
            return digest
        recipients = Subscriber.objects.filter(is_active=True).order_by('pk')
        Delivery.objects.bulk_create([
            Delivery(digest=digest, subscriber=s, email=s.email) for s in recipients
        ])
        digest.state = 'queued'
        digest.queued_at = timezone.now()
        digest.save(update_fields=['state', 'queued_at'])
        return digest


def settle(digest):
    """Caller holds the digest lock."""
    states = set(Delivery.objects.filter(digest=digest).values_list('state', flat=True))
    if states & {'failed', 'uncertain'}:
        digest.state = 'attention'
    elif 'sending' in states:
        digest.state = 'sending'
    elif 'pending' in states:
        digest.state = 'queued'
    else:
        digest.state = 'sent'
        digest.sent_at = digest.sent_at or timezone.now()
    digest.save(update_fields=['state', 'sent_at'])


def recover_stale():
    cutoff = timezone.now() - STALE_AFTER
    ids = Delivery.objects.filter(state='sending', attempted_at__lt=cutoff).values_list('digest_id', flat=True).distinct()
    for digest_id in list(ids):
        with transaction.atomic():
            digest = Digest.objects.select_for_update().get(pk=digest_id)
            Delivery.objects.filter(digest=digest, state='sending', attempted_at__lt=cutoff).update(
                state='uncertain', error='Обработчик прерван. Проверьте результат у SMTP-провайдера.')
            settle(digest)


def claim_next():
    # PostgreSQL locks the issue only while reserving a recipient. SMTP runs outside it.
    ids = Digest.objects.filter(state__in=['queued', 'sending', 'attention']).order_by('queued_at', 'pk').values_list('pk', flat=True)
    for digest_id in list(ids):
        with transaction.atomic():
            digest = Digest.objects.select_for_update().get(pk=digest_id)
            delivery = Delivery.objects.filter(digest=digest, state='pending').order_by('pk').first()
            if not delivery:
                settle(digest)
                continue
            if not Subscriber.objects.filter(pk=delivery.subscriber_id, is_active=True).exists():
                delivery.state = 'skipped'
                delivery.save(update_fields=['state'])
                settle(digest)
                return False
            delivery.state = 'sending'
            delivery.attempted_at = timezone.now()
            delivery.claim = uuid.uuid4()
            delivery.error = ''
            delivery.save(update_fields=['state', 'attempted_at', 'claim', 'error'])
            settle(digest)
            return delivery
    return None


def process_one():
    delivery = claim_next()
    if delivery is None:
        return False
    if delivery is False:
        return True
    subscriber = Subscriber.objects.get(pk=delivery.subscriber_id)
    # A second check covers unsubscribe between reservation and message construction.
    state, error = 'skipped', ''
    if subscriber.is_active:
        digest = delivery.digest
        unsubscribe = settings.SITE_URL.rstrip('/') + reverse('unsubscribe', args=[subscriber.token])
        html = digest.body + '<p><a href="{}">Отписаться от дайджеста</a></p>'.format(escape(unsubscribe))
        email = EmailMultiAlternatives(
            digest.subject, strip_tags(digest.body) + '\n\nОтписаться: ' + unsubscribe,
            settings.DEFAULT_FROM_EMAIL, [delivery.email],
        )
        email.attach_alternative(html, 'text/html')
        try:
            if not email.send():
                state, error = 'failed', 'SMTP не принял письмо.'
            else:
                state = 'sent'
        except smtplib.SMTPRecipientsRefused:
            state, error = 'failed', 'SMTP отклонил адрес получателя.'
        except Exception as exc:
            # Do not store backend text, which may include credentials or personal data.
            state, error = 'uncertain', f'{type(exc).__name__}: проверьте результат отправки у провайдера.'
    with transaction.atomic():
        digest = Digest.objects.select_for_update().get(pk=delivery.digest_id)
        Delivery.objects.filter(pk=delivery.pk, state='sending', claim=delivery.claim).update(
            state=state, error=error, sent_at=timezone.now() if state == 'sent' else None)
        settle(digest)
    return True


def resolve_delivery(delivery_id, decision):
    if decision not in ('retry', 'sent'):
        raise ValueError('Неизвестное действие.')
    with transaction.atomic():
        delivery = Delivery.objects.get(pk=delivery_id)
        digest = Digest.objects.select_for_update().get(pk=delivery.digest_id)
        delivery.refresh_from_db()
        if delivery.state not in ('failed', 'uncertain'):
            raise ValueError('Можно обработать только доставку с ошибкой или неизвестным результатом.')
        delivery.state = 'pending' if decision == 'retry' else 'sent'
        delivery.sent_at = timezone.now() if decision == 'sent' else None
        delivery.error = ''
        delivery.claim = None
        delivery.save(update_fields=['state', 'sent_at', 'error', 'claim'])
        settle(digest)


def heartbeat(name):
    DigestWorker.objects.update_or_create(name=name, defaults={'heartbeat': timezone.now()})
