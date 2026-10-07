from datetime import date, datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

import pytest
from django.template.loader import render_to_string

from apps.banners.models import Banner, Position
from apps.news.factories import ArticleFactory


@pytest.fixture
def placed_banner(db):
    banner = Banner.objects.create(
        name='Конференция Python', file_img='data-img/conference.png',
        link_to='https://example.org/conference',
        date_from=date(2026, 1, 1), date_to=None,
        date_days=254, date_time_from=0, date_time_to=24,
        priority=50, active=True,
    )
    banner.positions.set([
        Position.objects.get_or_create(tag=tag, defaults={'name': tag})[0]
        for tag in ('top', 'sidebar', 'article_end', 'bottom')
    ])
    with patch('apps.banners.templatetags.banner_tag.timezone.now',
               return_value=datetime(2026, 7, 6, 12, tzinfo=ZoneInfo('Europe/Moscow'))):
        yield banner


def test_home_shows_selected_slots_with_direct_image_url(client, placed_banner):
    html = client.get('/').content.decode()
    for slot in ('top', 'sidebar', 'bottom'):
        assert html.count(f'data-banner-position="{slot}"') == 1
    assert 'data-banner-position="article_end"' not in html
    assert html.count('href="https://example.org/conference"') == 3
    assert html.count('src="/media/data-img/conference.png"') == 3
    assert 'alt="Конференция Python"' in html
    assert html.index('data-banner-position="top"') < html.index('id="main-content"')
    assert html.index('data-banner-position="bottom"') > html.index('</main>')


def test_article_shows_article_slot_not_sidebar(client, placed_banner):
    article = ArticleFactory(is_our=True)
    html = client.get(article.get_absolute_url()).content.decode()
    assert 'data-banner-position="sidebar"' not in html
    for slot in ('top', 'article_end', 'bottom'):
        assert html.count(f'data-banner-position="{slot}"') == 1
    assert html.index('data-banner-position="article_end"') > html.index('</article>')


def test_archive_only_shows_global_slots(client, placed_banner):
    html = client.get('/materials/').content.decode()
    for slot in ('top', 'bottom'):
        assert html.count(f'data-banner-position="{slot}"') == 1
    for slot in ('sidebar', 'article_end'):
        assert f'data-banner-position="{slot}"' not in html


def test_disabling_or_unassigning_banner_removes_markup(client, placed_banner):
    placed_banner.active = False
    placed_banner.save()
    assert 'data-banner-position=' not in client.get('/').content.decode()
    placed_banner.active = True
    placed_banner.save()
    placed_banner.positions.clear()
    assert 'data-banner-position=' not in client.get('/').content.decode()


def test_banner_template_escapes_name_and_ignores_unsafe_legacy_dimensions(placed_banner):
    placed_banner.name = '<script>alert(1)</script>'
    placed_banner.width = '1px;position:fixed'
    placed_banner.height = '1px;background:url(https://example.org/track)'
    html = render_to_string('blocks/banner.html', {'banner': placed_banner, 'place': 'top'})
    assert '<script>' not in html
    assert '&lt;script&gt;' in html
    assert 'position:fixed' not in html
    assert 'background:url' not in html
    assert 'style="width: auto;"' in html
    assert 'style="max-height: none;"' in html


def test_server_error_page_does_not_query_banners():
    # No database access is permitted in this test: a DB outage must not prevent
    # the fallback error page from rendering.
    assert 'Не удалось открыть страницу' in render_to_string('500.html')
