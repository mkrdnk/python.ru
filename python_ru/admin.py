from urllib.parse import urlencode

from django.apps import apps
from django.contrib.admin import AdminSite
from django.urls import reverse


class EditorialAdminSite(AdminSite):
    site_header = 'Python.ru — редакция'
    site_title = 'Редакция Python.ru'
    index_title = 'Рабочий стол'
    index_template = 'admin/editorial_index.html'

    def get_app_list(self, request, app_label=None):
        original = super().get_app_list(request, app_label)
        groups = [
            ('editorial', 'Редакция', ['article', 'page', 'contribution']),
            ('catalogues', 'Каталоги и события', ['project', 'community', 'event', 'city']),
            ('mail', 'Рассылка', ['digest', 'subscriber', 'delivery']),
            ('advertising', 'Реклама', ['banner']),
            ('administration', 'Администрирование', ['user', 'group', 'link', 'position']),
        ]
        models = {m['object_name'].lower(): m for app in original for m in app['models']}
        result = []
        for label, title, names in groups:
            items = [models.pop(name) for name in names if name in models]
            if items:
                result.append(dict(name=title, app_label=label, app_url=items[0]['admin_url'],
                                   has_module_perms=True, models=items))
        if models:
            result.append(dict(name='Прочее', app_label='other', app_url='',
                               has_module_perms=True, models=list(models.values())))
        return result

    def index(self, request, extra_context=None):
        shortcuts = []
        for label, title, filters in [
            ('portal.Contribution', 'Новые предложения', {'status': 'new'}),
            ('news.Article', 'Черновики материалов', {'is_active': False}),
            ('portal.Page', 'Черновики страниц', {'is_active': False}),
            ('events.Event', 'Черновики событий', {'is_active': False}),
            ('portal.Project', 'Черновики проектов', {'is_active': False}),
            ('portal.Community', 'Черновики сообществ', {'is_active': False}),
            ('portal.Digest', 'Черновики дайджестов', {'state': 'draft'}),
        ]:
            model = apps.get_model(label)
            ma = self._registry[model]
            if ma.has_view_or_change_permission(request):
                shortcuts.append({'title': title, 'count': model.objects.filter(**filters).count(),
                                  'url': reverse(f'admin:{model._meta.app_label}_{model._meta.model_name}_changelist')
                                         + '?' + urlencode(filters)})
        return super().index(request, {**(extra_context or {}), 'shortcuts': shortcuts})
