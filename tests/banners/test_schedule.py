from datetime import date, datetime

import pytest
from django.utils import timezone

from apps.banners.models import Banner, Position
from apps.banners.templatetags.banner_tag import get_current_banner


def scheduled_banner(position, **changes):
    values = {
        'name': 'Баннер',
        'file_img': 'data-img/banner.png',
        'link_to': 'https://example.test/banner',
        'date_from': date(2025, 1, 1),
        'date_to': date(2025, 1, 31),
        'date_days': 2,
        'date_time_from': 10,
        'date_time_to': 12,
        'priority': 50,
        'active': True,
    }
    values.update(changes)
    banner = Banner.objects.create(**values)
    banner.positions.add(position)
    return banner


def local_time(year, month, day, hour):
    return timezone.make_aware(datetime(year, month, day, hour))


@pytest.mark.django_db
def test_schedule_uses_weekday_bits_inclusive_dates_and_exclusive_end_hour():
    top = Position.objects.get(tag='top')
    monday_at_eleven = local_time(2025, 1, 6, 11)
    banner = scheduled_banner(
        top,
        date_from=monday_at_eleven.date(),
        date_to=monday_at_eleven.date(),
        date_days=2,
    )

    assert get_current_banner('top', monday_at_eleven) == banner
    assert get_current_banner('top', local_time(2025, 1, 6, 12)) is None
    assert get_current_banner('top', local_time(2025, 1, 7, 11)) is None


@pytest.mark.django_db
def test_schedule_selects_highest_priority_then_lowest_primary_key_and_skips_unsafe_legacy_link():
    sidebar = Position.objects.get(tag='sidebar')
    now = local_time(2025, 1, 6, 11)
    first = scheduled_banner(sidebar, date_from=now.date(), date_to=None)
    scheduled_banner(sidebar, date_from=now.date(), date_to=None)
    unsafe = scheduled_banner(
        sidebar,
        date_from=now.date(),
        date_to=None,
        link_to='javascript:alert(1)',
        priority=100,
    )

    assert get_current_banner('sidebar', now) == first
    assert unsafe.priority > first.priority
    assert get_current_banner('unknown-slot', now) is None
