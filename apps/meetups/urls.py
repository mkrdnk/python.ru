from django.urls import re_path

from . import views


urlpatterns = [
    re_path(r'^(?P<event_slug>[\w-]+)/$', views.EventDetailView.as_view(), name='event_detail_view'),
]
