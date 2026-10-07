from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.db import connection, connections
from django.utils import timezone

from apps.portal.delivery import enqueue, process_one, claim_next, recover_stale, resolve_delivery
from apps.portal.models import Delivery, Digest, Subscriber

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def smtp(settings):
    settings.EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'


def issue():
    digest = Digest.objects.create(subject='Issue', body='<p>Hi</p>')
    subscriber = Subscriber.objects.create(email='one@example.org')
    return digest, subscriber


def test_fixed_audience_repeat_and_unsubscribe():
    digest, subscriber = issue()
    other = Subscriber.objects.create(email='two@example.org')
    enqueue(digest.pk)
    subscriber.email = 'changed@example.org'
    subscriber.save()
    other.is_active = False
    other.save()
    Subscriber.objects.create(email='late@example.org')
    enqueue(digest.pk)
    with patch('apps.portal.delivery.EmailMultiAlternatives.send', return_value=1) as send:
        while process_one():
            pass
        enqueue(digest.pk)
        assert not process_one()
        assert send.call_count == 1
    digest.refresh_from_db()
    assert digest.state == 'sent' and digest.sent_at
    assert list(digest.delivery_set.order_by('pk').values_list('email', 'state')) == [
        ('one@example.org', 'sent'), ('two@example.org', 'skipped')]


def test_uncertain_delivery_requires_explicit_decision():
    digest, _ = issue()
    enqueue(digest.pk)
    with patch('apps.portal.delivery.EmailMultiAlternatives.send', side_effect=TimeoutError('secret')):
        assert process_one()
    delivery = Delivery.objects.get()
    assert delivery.state == 'uncertain' and 'secret' not in delivery.error
    digest.refresh_from_db()
    assert digest.state == 'attention'
    assert not process_one()
    resolve_delivery(delivery.pk, 'retry')
    with patch('apps.portal.delivery.EmailMultiAlternatives.send', return_value=1):
        assert process_one()
    delivery.refresh_from_db()
    assert delivery.state == 'sent'
    with pytest.raises(ValueError):
        resolve_delivery(delivery.pk, 'retry')


def test_crashed_worker_never_automatically_resends():
    digest, _ = issue()
    enqueue(digest.pk)
    claimed = claim_next()
    Delivery.objects.filter(pk=claimed.pk).update(attempted_at=timezone.now() - timedelta(minutes=6))
    recover_stale()
    claimed.refresh_from_db()
    assert claimed.state == 'uncertain'
    assert not process_one()
    resolve_delivery(claimed.pk, 'sent')
    digest.refresh_from_db()
    assert digest.state == 'sent'


def test_empty_audience_completes():
    digest = Digest.objects.create(subject='Empty', body='Empty')
    enqueue(digest.pk)
    assert not process_one()
    digest.refresh_from_db()
    assert digest.state == 'sent'


@pytest.mark.django_db(transaction=True)
def test_concurrent_enqueue_and_workers_on_postgresql():
    if connection.vendor != 'postgresql':
        pytest.skip('Requires PostgreSQL row locks')
    digest, _ = issue()
    Subscriber.objects.create(email='two@example.org')

    def isolated(fn):
        try:
            return fn()
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(lambda _: isolated(lambda: enqueue(digest.pk)), range(2)))
    assert Delivery.objects.count() == 2
    with patch('apps.portal.delivery.EmailMultiAlternatives.send', return_value=1) as send:
        with ThreadPoolExecutor(max_workers=2) as pool:
            list(pool.map(lambda _: isolated(process_one), range(2)))
        assert send.call_count == 2
    assert Delivery.objects.filter(state='sent').count() == 2
    digest.refresh_from_db()
    assert digest.state == 'sent'
