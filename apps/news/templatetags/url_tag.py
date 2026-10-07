from urllib.parse import urlsplit

from django import template

register = template.Library()


@register.simple_tag
def get_host_from_url(url):
    try:
        return urlsplit(url or '').hostname or 'Источник'
    except ValueError:
        return 'Источник'


@register.filter
def compact_number(value):
    if value is None:
        return ''
    if value < 1000:
        return str(value)
    return format(value / 1000, '.1f').rstrip('0').rstrip('.') + 'k'
