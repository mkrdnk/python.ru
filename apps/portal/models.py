import uuid

from django_ckeditor_5.fields import CKEditor5Field
from django.conf import settings
from django.db import models
from django.db.models import Q
from django.urls import reverse


class DirectoryEntry(models.Model):
    name = models.CharField('Название', max_length=200)
    description = models.TextField('Описание', blank=True)
    url = models.URLField('Ссылка')
    is_active = models.BooleanField('Опубликовано', default=False)
    position = models.PositiveIntegerField('Порядок', default=0)

    class Meta:
        abstract = True
        ordering = ['position', 'name', 'pk']

    def __str__(self):
        return self.name


class Project(DirectoryEntry):
    category = models.CharField('Категория', max_length=50, blank=True)
    stars = models.PositiveIntegerField('Звёзды GitHub (необязательно)', null=True, blank=True)

    class Meta(DirectoryEntry.Meta):
        verbose_name = 'Open Source проект'
        verbose_name_plural = 'Open Source проекты'


class Community(DirectoryEntry):
    city = models.CharField('Город или регион', max_length=100)
    members = models.PositiveIntegerField('Участники (необязательно)', null=True, blank=True)

    class Meta(DirectoryEntry.Meta):
        verbose_name = 'Сообщество'
        verbose_name_plural = 'Сообщества'


class Page(models.Model):
    slug = models.SlugField('Адрес', unique=True)
    title = models.CharField('Заголовок', max_length=200)
    body = CKEditor5Field('Текст')
    is_active = models.BooleanField('Опубликовано', default=False)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('portal_page', args=[self.slug])

    class Meta:
        verbose_name = 'Страница'
        verbose_name_plural = 'Страницы'


class Contribution(models.Model):
    KINDS = [('article', 'Статья'), ('event', 'Событие'), ('project', 'Проект'), ('community', 'Сообщество')]
    kind = models.CharField('Тип', max_length=20, choices=KINDS)
    title = models.CharField('Название', max_length=200)
    name = models.CharField('Ваше имя', max_length=120)
    email = models.EmailField('Email для ответа')
    url = models.URLField('Ссылка', blank=True)
    description = models.TextField('Описание')
    created_at = models.DateTimeField('Получено', auto_now_add=True)
    assignee = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='Ответственный',
                                 null=True, blank=True, on_delete=models.SET_NULL)
    internal_note = models.TextField('Внутренний комментарий', blank=True)
    article = models.ForeignKey('news.Article', null=True, blank=True, on_delete=models.PROTECT)
    event = models.ForeignKey('events.Event', null=True, blank=True, on_delete=models.PROTECT)
    project = models.ForeignKey('Project', null=True, blank=True, on_delete=models.PROTECT)
    community = models.ForeignKey('Community', null=True, blank=True, on_delete=models.PROTECT)

    @property
    def target(self):
        return self.article or self.event or self.project or self.community

    status = models.CharField('Статус', max_length=20, default='new', choices=[
        ('new', 'Новое'), ('review', 'На рассмотрении'), ('done', 'Обработано')])

    def __str__(self):
        return self.title

    class Meta:
        constraints = [models.CheckConstraint(
            name='contribution_at_most_one_target',
            condition=(Q(article__isnull=True, event__isnull=True, project__isnull=True)
                       | Q(article__isnull=True, event__isnull=True, community__isnull=True)
                       | Q(article__isnull=True, project__isnull=True, community__isnull=True)
                       | Q(event__isnull=True, project__isnull=True, community__isnull=True)),
        )]
        ordering = ['-created_at']
        verbose_name = 'Предложение'
        verbose_name_plural = 'Предложения читателей'


class Subscriber(models.Model):
    email = models.EmailField('Email', unique=True)
    is_active = models.BooleanField('Подписан', default=True)
    created_at = models.DateTimeField('Дата подписки', auto_now_add=True)
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    def __str__(self):
        return self.email

    class Meta:
        verbose_name = 'Подписчик'
        verbose_name_plural = 'Подписчики'


class Digest(models.Model):
    STATES = [('draft', 'Черновик'), ('queued', 'В очереди'), ('sending', 'Отправляется'),
              ('attention', 'Требует внимания'), ('sent', 'Отправлен')]
    state = models.CharField('Состояние', max_length=12, choices=STATES, default='draft')
    queued_at = models.DateTimeField('Поставлен в очередь', null=True, blank=True, editable=False)
    subject = models.CharField('Тема письма', max_length=200)
    body = CKEditor5Field('Содержимое письма')
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField('Отправлено', null=True, blank=True, editable=False)

    def __str__(self):
        return self.subject

    class Meta:
        permissions = [('send_digest', 'Может отправлять дайджесты')]
        verbose_name = 'Выпуск дайджеста'
        verbose_name_plural = 'Выпуски дайджеста'


class Delivery(models.Model):
    STATES = [('pending', 'Ожидает'), ('sending', 'Отправляется'), ('sent', 'Доставлено'),
              ('skipped', 'Отписался'), ('failed', 'Ошибка'), ('uncertain', 'Результат неизвестен')]
    digest = models.ForeignKey(Digest, on_delete=models.CASCADE)
    subscriber = models.ForeignKey(Subscriber, on_delete=models.PROTECT)
    email = models.EmailField('Адрес на момент запуска', blank=True)
    state = models.CharField('Состояние', max_length=12, choices=STATES, default='pending')
    attempted_at = models.DateTimeField('Последняя попытка', null=True, blank=True)
    sent_at = models.DateTimeField('Доставлено', null=True, blank=True)
    error = models.TextField('Ошибка', blank=True)
    claim = models.UUIDField(null=True, editable=False)

    class Meta:
        verbose_name = 'Доставка'
        verbose_name_plural = 'Доставки'
        unique_together = [('digest', 'subscriber')]
        indexes = [models.Index(fields=['state', 'id'], name='delivery_queue_idx')]


class DigestWorker(models.Model):
    """Heartbeat only; deliveries are claimed independently by each worker."""
    name = models.CharField(max_length=100, primary_key=True)
    heartbeat = models.DateTimeField()
