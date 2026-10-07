from django.views.generic import DetailView

from apps.events.models import Event


class EventDetailView(DetailView):
    queryset = Event.objects.active().select_related('city').prefetch_related('talks__speaker__employer')
    slug_url_kwarg = 'event_slug'
    template_name = 'meetups/event_detail.html'
