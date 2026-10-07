import pytest
from django.contrib.auth.models import Group, Permission
from django.contrib.admin.models import LogEntry
from django.core.management import call_command
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from apps.events.models import City, Event
from apps.news.factories import ArticleFactory
from apps.news.models import Article
from apps.portal.models import Community, Contribution, Digest, Page, Project, Subscriber

pytestmark = pytest.mark.django_db


@pytest.fixture
def editor(django_user_model):
    call_command('setup_editor_roles', verbosity=0)
    user = django_user_model.objects.create_user('editor', is_staff=True)
    user.groups.add(Group.objects.get(name='Редакторы'))
    client = Client()
    client.force_login(user)
    return client, user


def article_payload(**extra):
    return dict(name='Новый материал', kind='article', author='Автор', description='Описание',
                text='<p>Текст</p>', tags='python', published_at_0='2026-10-07',
                published_at_1='12:00:00', url='https://example.org/original', **extra)


def test_editor_roles_navigation_and_direct_access(editor, admin_client):
    client, user = editor
    call_command('setup_editor_roles', verbosity=0)
    assert Group.objects.filter(name='Редакторы').count() == 1
    html = client.get('/admin/').content.decode()
    for label in ['Редакция', 'Каталоги и события', 'Рассылка', 'Новые предложения']:
        assert label in html
    for path in ['auth/user', 'auth/group', 'portal/subscriber', 'portal/delivery', 'banners/banner', 'content/link']:
        assert client.get('/admin/' + path + '/').status_code == 403
        assert admin_client.get('/admin/' + path + '/').status_code == 200
    assert not user.has_perm('news.delete_article')
    assert not user.has_perm('portal.send_digest')
    assert client.get('/admin/meetups/talk/').status_code == 404


def test_article_form_and_legacy_values(editor):
    client, _ = editor
    response = client.post(reverse('admin:news_article_add'), article_payload())
    assert response.status_code == 302, response.context['adminform'].form.errors
    article = Article.objects.get()
    assert (article.is_our, article.language, article.source, article.is_active) == (True, 'ru', 'python.ru', False)
    assert article.get_absolute_url() == f'/post/{article.pk}/'
    article.is_our, article.language, article.source, article.section = False, 'en', 'pythondigest', 'Legacy'
    article.save()
    url = reverse('admin:news_article_change', args=[article.pk])
    response = client.get(url)
    form = response.context['adminform'].form
    for field in ['source', 'language', 'is_our', 'section', 'external_id', 'is_featured']:
        assert field not in form.fields
    response = client.post(url, article_payload(is_our='on', language='ru', source='python.ru'))
    assert response.status_code == 302
    article.refresh_from_db()
    assert (article.is_our, article.language, article.source, article.section) == (False, 'en', 'pythondigest', 'Legacy')
    assert article.get_absolute_url() == 'https://example.org/original'


def test_image_filter_and_logged_publication(editor):
    client, user = editor
    empty = ArticleFactory(image='', is_active=False)
    ArticleFactory(image='articles/a.png')
    url = reverse('admin:news_article_changelist')
    response = client.get(url, {'image': 'no'})
    assert list(response.context['cl'].queryset) == [empty]
    assert client.post(url, {'action': 'publish', '_selected_action': [empty.pk]}).status_code == 302
    empty.refresh_from_db()
    assert empty.is_active
    assert LogEntry.objects.filter(user=user, object_id=str(empty.pk), change_message='Опубликовано').exists()


def test_preview_is_private_and_all_types_render(editor, client):
    staff, _ = editor
    city = City.objects.create(name='Москва')
    entries = [ArticleFactory(is_active=False, text='<script>window.preview_injection=1</script>'),
               Event.objects.create(name='Draft event', city=city, is_active=False),
               Project.objects.create(name='Draft project', url='https://example.org'),
               Community.objects.create(name='Draft community', city='Москва', url='https://example.org'),
               Page.objects.create(title='Draft page', slug='draft', body='<p>Пример</p>'),
               Digest.objects.create(subject='Draft digest', body='<p>Письмо</p>')]
    for obj in entries:
        url = reverse(f'admin:{obj._meta.app_label}_{obj._meta.model_name}_preview', args=[obj.pk])
        assert client.get(url).status_code == 302
        response = staff.get(url)
        assert response.status_code == 200
        assert 'no-store' in response.headers['Cache-Control']
        assert 'sandbox=""' in response.content.decode()
        from lxml import html
        document = html.fromstring(response.content)
        frame = document.xpath('//iframe')[0]
        assert '<html' in frame.attrib['srcdoc']
        assert not document.xpath('//script[contains(text(), "preview_injection")]')
    assert client.get(f'/post/{entries[0].pk}/').status_code == 404
    assert client.get(f'/events/{entries[1].pk}/').status_code == 404
    assert client.get('/pages/draft/').status_code == 404


@pytest.mark.parametrize('kind', ['article', 'event', 'project', 'community'])
def test_convert_proposal_once_and_keep_contact_private(editor, kind):
    client, user = editor
    city = City.objects.create(name='Москва')
    proposal = Contribution.objects.create(kind=kind, title='Предложение', name='Читатель',
                                          email='private@example.org', description='<script>secret()</script>')
    model = proposal._meta.get_field(kind).remote_field.model
    url = reverse(f'admin:{model._meta.app_label}_{model._meta.model_name}_add') + f'?contribution={proposal.pk}'
    response = client.get(url)
    assert response.status_code == 200
    assert response.context['adminform'].form.initial['is_active'] is False
    assert not model.objects.filter(name='Предложение').exists()
    if kind == 'article':
        payload = article_payload()
    elif kind == 'event':
        payload = {'name': 'Событие', 'city': city.pk, 'description_html': 'Описание'}
    else:
        payload = {'name': 'Запись', 'url': 'https://example.org', 'position': 0, 'city': 'Москва'}
    response = client.post(url, payload)
    assert response.status_code == 302, response.context['adminform'].form.errors
    proposal.refresh_from_db()
    assert proposal.target and not proposal.target.is_active
    assert proposal.status == 'review' and proposal.assignee == user
    target_pk = proposal.target.pk
    count = model.objects.count()
    assert client.post(url, payload).status_code == 302
    assert model.objects.count() == count
    proposal.refresh_from_db()
    assert proposal.target.pk == target_pk


def test_read_only_proposal_permission_cannot_convert(editor):
    client, user = editor
    user.groups.clear()
    user.user_permissions.add(*Permission.objects.filter(codename__in=['view_contribution', 'add_article']))
    proposal = Contribution.objects.create(kind='article', title='Private', email='x@example.org', description='Text')
    url = reverse('admin:news_article_add') + f'?contribution={proposal.pk}'
    assert client.get(url).status_code == 403
    assert client.post(url, article_payload()).status_code == 403


def test_digest_permissions_freeze_copy_and_csrf(editor, admin_client, admin_user, settings):
    settings.EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    client, _ = editor
    digest = Digest.objects.create(subject='Письмо', body='<p>Body</p>')
    Subscriber.objects.create(email='subscriber@example.org')
    send = reverse('admin:portal_digest_operation', args=[digest.pk, 'send'])
    assert client.get(send).status_code == 403
    assert client.post(send).status_code == 403
    assert admin_client.get(send).status_code == 200
    digest.refresh_from_db()
    assert digest.state == 'draft'
    secure = Client(enforce_csrf_checks=True)
    secure.force_login(admin_user)
    assert secure.post(send).status_code == 403
    assert admin_client.post(send).status_code == 302
    digest.refresh_from_db()
    assert digest.state == 'queued'
    change = reverse('admin:portal_digest_change', args=[digest.pk])
    assert client.post(change, {'subject': 'Changed', 'body': 'Changed'}).status_code == 302
    digest.refresh_from_db()
    assert digest.subject == 'Письмо'
    assert client.post(reverse('admin:portal_digest_operation', args=[digest.pk, 'copy'])).status_code == 302
    assert Digest.objects.filter(state='draft', subject='Письмо').count() == 1
    assert admin_client.get(reverse('admin:portal_digest_delete', args=[digest.pk])).status_code == 403


@pytest.mark.django_db(transaction=True)
def test_concurrent_proposal_conversion_on_postgresql(django_user_model):
    from concurrent.futures import ThreadPoolExecutor
    from django.db import connection, connections
    if connection.vendor != 'postgresql':
        pytest.skip('Requires PostgreSQL row locks')
    call_command('setup_editor_roles', verbosity=0)
    user = django_user_model.objects.create_user('concurrent-editor', is_staff=True)
    user.groups.add(Group.objects.get(name='Редакторы'))
    proposal = Contribution.objects.create(kind='project', title='Project', description='Text', email='private@example.org')
    url = reverse('admin:portal_project_add') + f'?contribution={proposal.pk}'
    clients = [Client(), Client()]
    for client in clients:
        client.force_login(user)

    def submit(client):
        try:
            return client.post(url, {'name': 'Project', 'url': 'https://example.org', 'position': 0}).status_code
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert list(pool.map(submit, clients)) == [302, 302]
    proposal.refresh_from_db()
    assert proposal.project_id and Project.objects.count() == 1
