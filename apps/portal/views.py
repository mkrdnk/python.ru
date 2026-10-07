import uuid

from django.contrib.syndication.views import Feed
from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.views.generic import ListView, DetailView
from django.views.decorators.http import require_http_methods

from apps.events.models import Event
from apps.news.models import Article
from apps.portal.forms import ContributionForm, SubscribeForm
from apps.portal.models import Community, Page, Project, Subscriber


class DirectoryView(ListView):
    template_name = 'portal/directory.html'
    paginate_by = 24
    section = 'projects'

    def get_queryset(self):
        if self.section == 'events':
            return Event.objects.active().select_related('city').order_by('-date', '-pk')
        model = Project if self.section == 'projects' else Community
        return model.objects.filter(is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(section=self.section, title={
            'projects': 'Open Source', 'community': 'Сообщества', 'events': 'События',
        }[self.section])
        return context


class PageView(DetailView):
    queryset = Page.objects.filter(is_active=True)
    template_name = 'portal/page.html'


@require_http_methods(['GET', 'POST'])
def contribute(request):
    kind = request.GET.get('kind', 'article')
    form = ContributionForm(request.POST or None, initial={'kind': kind})
    if request.method == 'POST' and form.is_valid():
        if not form.cleaned_data['website']:
            form.save()
        return render(request, 'portal/success.html', {'title': 'Спасибо за предложение',
                      'message': 'Редакция рассмотрит материал. Если понадобятся детали, мы свяжемся с вами по email.'})
    return render(request, 'portal/form.html', {'form': form, 'title': 'Предложить материал',
                  'intro': 'Статья, событие, проект или сообщество — расскажите, чем хотите поделиться.',
                  'button': 'Отправить на рассмотрение'})


@require_http_methods(['GET', 'POST'])
def subscribe(request):
    form = SubscribeForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        if not form.cleaned_data['website']:
            email = form.cleaned_data['email'].strip().lower()
            Subscriber.objects.get_or_create(email=email)
        return render(request, 'portal/success.html', {'title': 'Заявка на подписку принята',
                      'message': 'Если этот адрес ещё не подписан, он добавлен в список дайджеста. '
                                 'Отписаться можно по ссылке в любом выпуске.'})
    return render(request, 'portal/form.html', {'form': form, 'title': 'Дайджест Python.ru',
                  'intro': 'Главные материалы, новости и события — без шума.', 'button': 'Подписаться'})


@require_http_methods(['GET', 'POST'])
def unsubscribe(request, token):
    try:
        token = uuid.UUID(token)
    except ValueError:
        raise Http404
    subscriber = get_object_or_404(Subscriber, token=token)
    if request.method == 'POST':
        subscriber.is_active = False
        subscriber.save(update_fields=['is_active'])
        return render(request, 'portal/success.html', {'title': 'Вы отписались',
                      'message': 'Дайджест больше не будет приходить на этот адрес.'})
    return render(request, 'portal/form.html', {'title': 'Отписаться от дайджеста',
                  'intro': 'Нажмите кнопку, чтобы прекратить получение писем.', 'button': 'Отписаться'})


class LatestFeed(Feed):
    title = 'Python.ru — материалы сообщества'
    link = '/materials/'
    description = 'Новости, статьи и заметки Python-сообщества.'

    def items(self):
        return Article.objects.active().order_by('-published_at', '-pk')[:30]

    def item_title(self, item):
        return item.name

    def item_description(self, item):
        return item.description

    def item_link(self, item):
        return item.get_absolute_url()

    def item_pubdate(self, item):
        return item.published_at
