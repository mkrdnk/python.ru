from datetime import timezone as datetime_timezone
import pytest
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from apps.events.models import City, Event
from apps.meetups.models import Employer, Speaker, Talk
from apps.news.factories import ArticleFactory


@pytest.mark.django_db
def test_search_keeps_query_when_loading_more(client):
    ArticleFactory.create_batch(12, name='Async Python', published_at=timezone.now())
    ArticleFactory(name='Unrelated', description='Nothing relevant', published_at=timezone.now())
    response = client.get('/', {'q': 'Async'})
    assert len(response.context['articles']) == 10
    assert 'q=Async' in response.context['next_url']
    page = client.get(response.context['next_url'] + '&fragment=1')
    assert len(page.context['articles']) == 2
    assert page.context['next_url'] is None
    empty = client.get('/', {'q': 'missing'})
    assert 'Материалы не найдены' in empty.content.decode()
    assert 'Сбросить поиск' in empty.content.decode()


@pytest.mark.django_db
def test_article_uses_own_date_and_rich_content(client):
    post = ArticleFactory(name='Article title', published_at=timezone.datetime(2020, 5, 4, tzinfo=datetime_timezone.utc),
                          is_our=True, text='<h2>Example</h2><pre><code>print(42)</code></pre>')
    ArticleFactory(is_featured=True, published_at=timezone.now())
    response = client.get(reverse('post_page', args=[post.pk]))
    html = response.content.decode()
    assert '4 мая 2020' in html
    assert '<pre><code>print(42)</code></pre>' in html
    assert 'К публикациям' in html
    assert 'css/site.css' in html
    for old in ['js-masonry', 'jquery', 'Telegram Группа', 'ЧТО ПОЛЕЗНОГО', 'plus.google.com']:
        assert old not in html


@pytest.mark.django_db
@override_settings(DEBUG=False)
def test_missing_or_inactive_article_is_friendly_404(client):
    post = ArticleFactory(is_active=False)
    for pk in [post.pk, post.pk + 100]:
        response = client.get(reverse('post_page', args=[pk]))
        assert response.status_code == 404
        assert 'Страница не найдена' in response.content.decode()
        assert 'css/site.css' in response.content.decode()


@pytest.mark.django_db
def test_meetup_without_avatar_and_with_embedded_media(client):
    city = City.objects.create(name='Москва')
    event = Event.objects.create(name='Python Meetup', slug='test-meetup', city=city,
                                 description_html='<p>Описание встречи</p>',
                                 is_registration_available=True, register_url='https://example.org/register')
    employer = Employer.objects.create(name='Company')
    speaker = Speaker.objects.create(first_name='Имя', last_name='Фамилия', employer=employer)
    Talk.objects.create(event=event, speaker=speaker, title='Доклад', description='<p>Описание доклада</p>',
                        video_url='<iframe src="https://example.org/video" title="Видео"></iframe>')
    response = client.get('/meetups/test-meetup/')
    html = response.content.decode()
    assert response.status_code == 200
    for expected in ['Python Meetup', 'Описание встречи', 'Доклад', 'Имя Фамилия',
                     'https://example.org/register', '<iframe', 'css/site.css', 'К публикациям']:
        assert expected in html
    assert 'Немного о нас' not in html
    assert 'Ближайшие события' not in html
    assert 'jquery' not in html


@pytest.mark.django_db
def test_search_is_case_insensitive_for_russian_and_treats_regex_as_text(client):
    article = ArticleFactory(name='Асинхронный Python [3.9]', published_at=timezone.now())
    for query in ['асинхронный', '[3.9]']:
        response = client.get('/', {'q': query})
        assert [item.pk for item in response.context['articles']] == [article.pk]
    assert not client.get('/', {'q': '.*'}).context['articles']
