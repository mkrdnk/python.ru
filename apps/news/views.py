import re
from urllib.parse import urlencode

from django.core import signing
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_datetime
from django.views.generic import RedirectView
from django.views.generic import TemplateView

from apps.news.models import Article
from apps.events.models import Event
from apps.portal.models import Project, Community


class IndexView(TemplateView):
    template_name = 'index.html'

    section = 'home'
    page_size = 10
    cursor_salt = 'news-feed'

    def get_template_names(self):
        if self.request.GET.get('fragment') == '1':
            return ['blocks/news_page.html']
        return [self.template_name]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        articles = Article.objects.active().order_by('-published_at', '-id')
        query = self.request.GET.get('q', '').strip()[:200]
        context['query'] = query
        if self.section == 'notes':
            articles = articles.filter(kind='note')
        elif not query:
            articles = articles.exclude(kind='note')
        if query:
            # SQLite LIKE does not case-fold Cyrillic; an escaped regex is literal
            # and supports case-insensitive Unicode search on both SQLite and PostgreSQL.
            pattern = re.escape(query)
            articles = articles.filter(Q(name__iregex=pattern) | Q(description__iregex=pattern) | Q(author__iregex=pattern))
        cursor = self.request.GET.get('cursor')
        if cursor:
            try:
                timestamp, article_id = signing.loads(cursor, salt=self.cursor_salt)
                published_at = parse_datetime(timestamp)
                if published_at is None or type(article_id) is not int:
                    raise ValueError
            except (signing.BadSignature, ValueError, TypeError):
                raise Http404('Invalid feed cursor')
            articles = articles.filter(
                Q(published_at__lt=published_at) |
                Q(published_at=published_at, id__lt=article_id)
            )
        is_home = self.section == 'home' and not query and not cursor
        page_size = 6 if is_home else self.page_size
        batch = list(articles[:page_size + 1])
        context['articles'] = batch[:page_size]
        context['next_url'] = None
        if len(batch) > page_size:
            last = context['articles'][-1]
            cursor = signing.dumps(
                [last.published_at.isoformat(), last.pk], salt=self.cursor_salt
            )
            params = {'cursor': cursor}
            if query:
                params['q'] = query
            context['next_url'] = '?' + urlencode(params)
        context['feed_articles'] = context['articles']
        context['section'] = self.section
        context['title'] = 'Заметки сообщества' if self.section == 'notes' else 'Все материалы'
        context['is_home'] = is_home
        if context['is_home'] and self.request.GET.get('fragment') != '1':
            context['lead_articles'] = context['articles'][:3]
            context['feed_articles'] = context['articles'][3:]
            context['notes'] = Article.objects.active().filter(kind='note')[:3]
            context['events'] = Event.objects.upcoming().select_related('city')[:4]
            context['projects'] = Project.objects.filter(is_active=True)[:4]
            context['communities'] = Community.objects.filter(is_active=True)[:4]
        if query:
            context['title'] = 'Результаты поиска'
            context['search_projects'] = Project.objects.filter(is_active=True).filter(
                Q(name__iregex=pattern) | Q(description__iregex=pattern))[:6]
            context['search_communities'] = Community.objects.filter(is_active=True).filter(
                Q(name__iregex=pattern) | Q(city__iregex=pattern))[:6]
            context['search_events'] = Event.objects.active().filter(name__iregex=pattern)[:6]
        return context


class PostView(TemplateView):
    template_name = 'post.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['post'] = get_object_or_404(Article.objects.active(), pk=self.kwargs['pk'])
        return context


class JuniorView(RedirectView):
    permanent = True

    def get_redirect_url(self, *args, **kwargs):
        return '/meetups/junior/'  # FIXME: make this alive
