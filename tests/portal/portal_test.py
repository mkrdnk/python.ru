from io import StringIO
from unittest.mock import patch

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import Client, override_settings
from django.utils import timezone

from apps.events.models import City, Event
from apps.news.factories import ArticleFactory
from apps.portal.models import Community, Contribution, Delivery, Digest, Project, Subscriber


@pytest.mark.django_db
def test_home_and_catalogues_use_published_content(client):
    for kind in ['interview', 'news', 'article', 'translation', 'note']:
        ArticleFactory(name='Published ' + kind, kind=kind, published_at=timezone.now())
    project = Project.objects.create(name='Published project', url='https://example.org/project', is_active=True)
    Project.objects.create(name='Hidden project', url='https://example.org/hidden')
    city = City.objects.create(name='Москва')
    event = Event.objects.create(name='Published event', city=city, date=timezone.now())
    Event.objects.create(name='Hidden event', city=city, is_active=False)
    Community.objects.create(name='Test community', city='Москва', url='https://example.org/community', is_active=True)
    home = client.get('/').content.decode()
    for expected in ['Published note', project.name, event.name, 'Test community']:
        assert expected in home
    assert 'Hidden project' not in home
    assert 'Hidden event' not in home
    assert len(client.get('/notes/').context['articles']) == 1
    assert all(a.kind != 'note' for a in client.get('/materials/').context['articles'])
    for path in ['/projects/', '/community/', '/events/', '/pages/about/', '/pages/editorial/', '/search/']:
        assert client.get(path).status_code == 200
    assert client.get(event.get_absolute_url()).status_code == 200
    assert client.get('/events/{}/'.format(event.pk + 1)).status_code == 404


@pytest.mark.django_db
def test_subscribe_validate_deduplicate_and_unsubscribe(client):
    assert client.post('/subscribe/', {'email': 'bad'}).context['form'].errors
    for email in ['Reader@example.org', 'reader@example.org']:
        response = client.post('/subscribe/', {'email': email})
        assert 'Заявка на подписку принята' in response.content.decode()
    assert Subscriber.objects.count() == 1
    subscriber = Subscriber.objects.get()
    url = '/unsubscribe/{}/'.format(subscriber.token)
    assert client.get(url).status_code == 200
    subscriber.refresh_from_db()
    assert subscriber.is_active
    client.post(url)
    subscriber.refresh_from_db()
    assert not subscriber.is_active
    assert client.get('/unsubscribe/00000000-0000-0000-0000-000000000000/').status_code == 404
    client.post('/subscribe/', {'email': 'bot@example.org', 'website': 'spam'})
    assert Subscriber.objects.count() == 1


@pytest.mark.django_db
def test_contribution_stays_private_until_editor_reviews(client):
    payload = {'kind': 'project', 'title': 'Proposed project', 'name': 'Reader', 'email': 'reader@example.org',
               'url': 'https://example.org', 'description': 'Description'}
    assert client.post('/contribute/', payload).status_code == 200
    assert Contribution.objects.get().status == 'new'
    assert not Project.objects.filter(name=payload['title']).exists()
    assert payload['email'] not in client.get('/projects/').content.decode()
    assert client.post('/contribute/', {'title': 'Incomplete'}).context['form'].errors
    assert Client(enforce_csrf_checks=True).post('/subscribe/', {'email': 'x@example.org'}).status_code == 403


@pytest.mark.django_db
def test_rss_and_search(client):
    post = ArticleFactory(is_our=True, published_at=timezone.now(), name='Async Python')
    ArticleFactory(is_active=False, name='Hidden post')
    Project.objects.create(name='Async Project', url='https://example.org', is_active=True)
    assert client.get('/rss/').status_code == 200
    xml = client.get('/rss/').content.decode()
    assert post.name in xml
    assert 'Hidden post' not in xml
    assert 'Async Project' in client.get('/search/', {'q': 'async'}).content.decode()


@pytest.mark.django_db
def test_digest_dry_run_and_retry_dont_resend(client):
    digest = Digest.objects.create(subject='Test digest', body='<p>Hello</p>')
    Subscriber.objects.create(email='active@example.org')
    Subscriber.objects.create(email='inactive@example.org', is_active=False)
    output = StringIO()
    call_command('send_digest', digest.pk, stdout=output)
    assert '1 recipients; no email sent' in output.getvalue()
    assert not Delivery.objects.exists()
    with override_settings(EMAIL_BACKEND='django.core.mail.backends.console.EmailBackend'):
        with pytest.raises(CommandError):
            call_command('send_digest', digest.pk, send=True)
    with override_settings(EMAIL_BACKEND='django.core.mail.backends.smtp.EmailBackend'):
        with patch('apps.portal.management.commands.send_digest.EmailMultiAlternatives.send', return_value=1) as send:
            call_command('send_digest', digest.pk, send=True, stdout=StringIO())
            call_command('send_digest', digest.pk, send=True, stdout=StringIO())
            assert send.call_count == 1
    assert Delivery.objects.count() == 1


@pytest.mark.django_db
def test_home_keeps_reference_layout_when_more_articles_exist(client):
    ArticleFactory.create_batch(15, published_at=timezone.now())
    response = client.get('/')
    assert response.context['is_home'] is True
    assert len(response.context['lead_articles']) == 3
    assert len(response.context['feed_articles']) == 3
    assert response.context['next_url']
    html = response.content.decode()
    for section in ['intro container', 'lead-grid', 'content-layout', 'notes-section',
                    'open-source-section', 'community-section', 'footer-top']:
        assert section in html
    more = client.get(response.context['next_url'] + '&fragment=1')
    first_ids = {a.pk for a in response.context['articles']}
    assert not first_ids.intersection(a.pk for a in more.context['articles'])
