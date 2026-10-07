from django import template
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.template.loader import render_to_string
from django.utils import timezone

from apps.banners.models import Banner, SUPPORTED_SLOT_TAGS, safe_url_validator

register = template.Library()


def is_safe_link(link):
    """Legacy rows bypassed model validation, so check them before rendering."""
    try:
        safe_url_validator(link)
    except ValidationError:
        return False
    return True


def get_current_banner(place, now=None):
    """Return the banner scheduled for a supported slot, or ``None``."""
    if place not in SUPPORTED_SLOT_TAGS:
        return None

    now = timezone.localtime(now or timezone.now())
    today = now.date()
    weekday_bit = 1 << (now.weekday() + 1)

    candidates = Banner.objects.filter(
        active=True,
        positions__tag=place,
        date_from__lte=today,
        date_time_from__lte=now.hour,
        date_time_to__gt=now.hour,
        file_img__isnull=False,
    ).filter(
        Q(date_to__isnull=True) | Q(date_to__gte=today),
    ).exclude(
        file_img='',
    ).distinct().order_by('-priority', 'pk')

    for banner in candidates:
        if banner.date_days & weekday_bit and is_safe_link(banner.link_to):
            return banner
    return None


@register.simple_tag
def get_banner(place):
    """Render the currently scheduled banner for ``place``."""
    banner = get_current_banner(place)
    if banner is None:
        return ''
    return render_to_string('blocks/banner.html', {
        'banner': banner,
        'place': place,
    })
