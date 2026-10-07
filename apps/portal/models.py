import uuid

from django_ckeditor_5.fields import CKEditor5Field
from django.db import models
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
    status = models.CharField('Статус', max_length=20, default='new', choices=[
        ('new', 'Новое'), ('review', 'На рассмотрении'), ('done', 'Обработано')])

    def __str__(self):
        return self.title

    class Meta:
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
    subject = models.CharField('Тема письма', max_length=200)
    body = CKEditor5Field('Содержимое письма')
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField('Отправлено', null=True, blank=True, editable=False)

    def __str__(self):
        return self.subject

    class Meta:
        verbose_name = 'Выпуск дайджеста'
        verbose_name_plural = 'Выпуски дайджеста'


class Delivery(models.Model):
    digest = models.ForeignKey(Digest, on_delete=models.CASCADE)
    subscriber = models.ForeignKey(Subscriber, on_delete=models.CASCADE)
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('digest', 'subscriber')]
