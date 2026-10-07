from django.db import models
from django.urls import reverse
from django.db.models import QuerySet
from model_utils.models import TimeStampedModel
from django.utils import timezone
from django_ckeditor_5.fields import CKEditor5Field


class City(TimeStampedModel):
    name = models.CharField('Название города', max_length=256)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Город'
        verbose_name_plural = 'Города'
        ordering = ['-id']


class EventQuerySet(QuerySet):

    def active(self):
        return self.filter(is_active=True)

    def upcoming(self):
        return self.active().filter(date__date__gte=timezone.localdate())


class Event(TimeStampedModel):
    name = models.CharField('Название события', max_length=256)
    city = models.ForeignKey(City, verbose_name='Город', on_delete=models.PROTECT)
    date = models.DateTimeField('Начало события', blank=True, null=True)
    is_active = models.BooleanField('Отображается на сайте', default=True)
    url = models.URLField('Ссылка на событие', blank=True)
    slug = models.SlugField(default='none', editable=False)
    description_html = CKEditor5Field('Описание', null=True, blank=True)

    objects = EventQuerySet.as_manager()

    def get_absolute_url(self):
        return self.url or reverse('event_by_id', args=[self.pk])

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Событие'
        verbose_name_plural = 'События'
        ordering = ['date', '-id']
