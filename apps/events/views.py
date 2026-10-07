from django.http import HttpResponseGone, HttpResponsePermanentRedirect
from django.urls import reverse
from django.views.generic import DetailView

from apps.events.models import Event


class EventDetailView(DetailView):
    queryset = Event.objects.active().select_related('city')
    template_name = 'events/detail.html'


def legacy_event(request, event_slug):
    matches = list(Event.objects.active().filter(slug=event_slug).values_list('pk', flat=True)[:2])
    if len(matches) != 1:
        return HttpResponseGone('Эта страница мероприятия больше недоступна.')
    return HttpResponsePermanentRedirect(reverse('event_by_id', args=[matches[0]]))
