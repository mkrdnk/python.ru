from django.db import models
from django.urls import reverse
from django.db.models import QuerySet
from model_utils import Choices
from model_utils.models import TimeStampedModel
from django_ckeditor_5.fields import CKEditor5Field


class ArticleQuerySet(QuerySet):

    def active(self):
        return self.filter(is_active=True)

    def featured(self):
        article = self.active().filter(is_featured=True).first()
        if not article:
            article = self.active().first()
        return article


class Article(TimeStampedModel):
    kind = models.CharField('Тип материала', max_length=20, default='article', choices=[
        ('article', 'Статья'), ('translation', 'Перевод'), ('interview', 'Интервью'),
        ('news', 'Новость'), ('note', 'Заметка')])
    author = models.CharField('Автор', max_length=200, blank=True)
    tags = models.CharField('Теги через запятую', max_length=300, blank=True)
    reading_minutes = models.PositiveIntegerField('Время чтения, минут', null=True, blank=True)
    url = models.URLField('URL', blank=True, null=True)
    name = models.CharField('Заголовок', max_length=1024)
    description = models.TextField('Описание', blank=True)
    text = CKEditor5Field('Текст', blank=True, default='')
    is_our = models.BooleanField('Наш пост?', default=False)
    published_at = models.DateTimeField('Дата публикации')
    section = models.CharField('Категория', max_length=100, blank=True)
    language = models.CharField('Язык', max_length=2, choices=Choices(('ru', '🇷🇺'), ('en', '🇬🇧')))
    source = models.CharField('Источник', max_length=32, choices=Choices('pythondigest', 'python.ru'))
    external_id = models.CharField('Внешний ID', max_length=32, unique=True, blank=True, null=True, editable=False)
    image = models.ImageField('Изображение', blank=True, upload_to='articles')
    is_active = models.BooleanField('Показывать', default=False)
    is_featured = models.BooleanField('Главная новость', default=False)

    objects = ArticleQuerySet.as_manager()

    def get_absolute_url(self):
        if self.is_our or not self.url:
            return reverse('post_page', args=[self.pk])
        return self.url

    @property
    def tag_list(self):
        return [tag.strip() for tag in self.tags.split(',') if tag.strip()]

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Новость'
        verbose_name_plural = 'Новости'
        ordering = ['-published_at', '-id']
