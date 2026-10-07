import datetime

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.news.factories import ArticleFactory


@pytest.mark.django_db
def test_feed_pages_are_stable(client):
    date = timezone.now()
    articles = [ArticleFactory(published_at=date) for _ in range(23)]
    ArticleFactory(is_active=False, published_at=date)
    first = client.get(reverse('materials'))
    assert [a.pk for a in first.context['articles']] == [a.pk for a in reversed(articles[13:])]
    ArticleFactory(published_at=date + datetime.timedelta(seconds=1))
    second = client.get(first.context['next_url'] + '&fragment=1')
    assert [a.pk for a in second.context['articles']] == [a.pk for a in reversed(articles[3:13])]
    assert b'<html' not in second.content
    third = client.get(second.context['next_url'])
    assert [a.pk for a in third.context['articles']] == [a.pk for a in reversed(articles[:3])]
    assert third.context['next_url'] is None
    assert b'<html' in third.content


@pytest.mark.django_db
def test_feed_content_and_shell(client):
    own = ArticleFactory(is_our=True, image='articles/test.jpg', description='<p>Описание</p>')
    external = ArticleFactory(url='https://example.org/article', is_featured=True)
    response = client.get('/')
    html = response.content.decode()
    assert reverse('post_page', args=[own.pk]) in html
    assert external.url in html
    assert b'/media/articles/test.jpg' in client.get(reverse('post_page', args=[own.pk])).content
    assert 'Описание' in html
    assert 'https://moscowpython.ru/' in html
    assert 'https://t.me/moscow_python' in html
    assert 'https://www.youtube.com/moscowdjangoru' in html
    assert 'class="logo site-logo" href="/"' in html
    for removed in ['js-masonry', 'id="about"', 'id="resources"',
                    'Geekfactor', 'nav-opener', 'Telegram Группа']:
        assert removed not in html
    assert client.get(reverse('post_page', args=[own.pk])).status_code == 200


@pytest.mark.django_db
def test_empty_feed_and_invalid_cursor(client):
    response = client.get('/')
    assert 'Публикаций пока нет.' in response.content.decode()
    assert response.context['next_url'] is None
    assert client.get('/?cursor=invalid').status_code == 404


@pytest.mark.django_db
def test_exact_page_does_not_offer_empty_page(client):
    ArticleFactory.create_batch(10)
    response = client.get('/materials/')
    assert len(response.context['articles']) == 10
    assert response.context['next_url'] is None
