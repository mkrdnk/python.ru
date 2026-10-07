from django.contrib import admin
from apps.events.models import Event, City
from python_ru.admin_mixins import ContributionTargetMixin, PreviewAdminMixin, PublishAdminMixin


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    search_fields = ['name']
    ordering = ['name']


@admin.register(Event)
class EventAdmin(ContributionTargetMixin, PreviewAdminMixin, PublishAdminMixin, admin.ModelAdmin):
    list_display = ['name', 'city', 'date', 'is_active']
    list_filter = ['is_active', 'city']
    search_fields = ['name', 'city__name']
    list_select_related = ['city']
    autocomplete_fields = ['city']
    ordering = ['-date', '-pk']
    date_hierarchy = 'date'
    fields = ['name', 'city', 'date', 'description_html', 'url', 'is_active']
    preview_template = 'events/detail.html'

    def get_changeform_initial_data(self, request):
        return {'is_active': False, **super().get_changeform_initial_data(request)}
