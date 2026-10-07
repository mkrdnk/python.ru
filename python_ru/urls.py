from django.conf import settings
from django.urls import include, re_path
from django.conf.urls.static import static
from django.contrib import admin

from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from apps.news import views as news_views
from apps.portal import views as portal_views
from apps.meetups.views import EventDetailView


urlpatterns = [
    re_path(r'^$', news_views.IndexView.as_view(), name='index'),
    re_path(r'^meetups/', include('apps.meetups.urls')),
    re_path(r'^junior/$', news_views.JuniorView.as_view(), name='junior'),
    re_path(r'^post/(?P<pk>\d+)/$', news_views.PostView.as_view(), name='post_page'),

    re_path(r'^materials/$', news_views.IndexView.as_view(section='materials'), name='materials'),
    re_path(r'^notes/$', news_views.IndexView.as_view(section='notes'), name='notes'),
    re_path(r'^search/$', news_views.IndexView.as_view(section='search'), name='search'),
    re_path(r'^events/$', portal_views.DirectoryView.as_view(section='events'), name='events'),
    re_path(r'^events/(?P<pk>\d+)/$', EventDetailView.as_view(), name='event_by_id'),
    re_path(r'^projects/$', portal_views.DirectoryView.as_view(section='projects'), name='projects'),
    re_path(r'^community/$', portal_views.DirectoryView.as_view(section='community'), name='community'),
    re_path(r'^pages/(?P<slug>[\w-]+)/$', portal_views.PageView.as_view(), name='portal_page'),
    re_path(r'^contribute/$', portal_views.contribute, name='contribute'),
    re_path(r'^subscribe/$', portal_views.subscribe, name='subscribe'),
    re_path(r'^unsubscribe/(?P<token>[0-9a-f-]{36})/$', portal_views.unsubscribe, name='unsubscribe'),
    re_path(r'^rss/$', portal_views.LatestFeed(), name='rss'),
    re_path(r'^admin/', admin.site.urls),
    re_path(r'^ckeditor/', include('django_ckeditor_5.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += staticfiles_urlpatterns()
