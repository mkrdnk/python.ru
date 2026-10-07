import re

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator, URLValidator
from django.db import models
from django.utils import timezone


SLOT_POSITIONS = (
    ('top', 'Под шапкой'),
    ('sidebar', 'В сайдбаре главной страницы'),
    ('article_end', 'После статьи'),
    ('bottom', 'Перед подвалом'),
)
SUPPORTED_SLOT_TAGS = tuple(tag for tag, _ in SLOT_POSITIONS)

WEEKDAY_CHOICES = (
    (2, 'Понедельник'),
    (4, 'Вторник'),
    (8, 'Среда'),
    (16, 'Четверг'),
    (32, 'Пятница'),
    (64, 'Суббота'),
    (128, 'Воскресенье'),
)
WEEKDAY_MASK = sum(value for value, _ in WEEKDAY_CHOICES)

DIMENSION_PATTERN = r'^[1-9]\d*(?:px|%)$'
dimension_validator = RegexValidator(
    regex=DIMENSION_PATTERN,
    message='Укажите положительное целое значение в px или % (например, 300px или 100%).',
)
safe_url_validator = URLValidator(schemes=['http', 'https'])


class Position(models.Model):
    name = models.CharField(max_length=255, verbose_name='Название места где будет размещатся банер')
    tag = models.CharField(max_length=32, verbose_name='Тег места размещения')

    def __str__(self):
        return 'Расположение {}'.format(self.name)

    @property
    def is_supported_slot(self):
        return self.tag in SUPPORTED_SLOT_TAGS

    class Meta:
        verbose_name = "Расположение"
        verbose_name_plural = "Расположение баннеров"


class Banner(models.Model):
    name = models.CharField(max_length=255, blank=False, verbose_name='Название баннера',
                            help_text='Назовите баннер так, чтобы было удобно в дальнейшем '
                                      'определять его среди других баннеров')
    file_swf = models.FileField(upload_to='data/', verbose_name='Swf-файл', blank=True, null=True)
    file_img = models.FileField(upload_to='data-img/', verbose_name='Файл изображения', blank=True, null=True)
    width = models.CharField(max_length=7, blank=True, verbose_name='Ширина отображения баннера',
                             help_text='Положительное целое значение в px или %, например 720px или 100%.',
                             validators=[dimension_validator])
    height = models.CharField(max_length=7, blank=True, verbose_name='Высота отображения баннера',
                              help_text='Положительное целое значение в px или %, например 200px или 100%.',
                              validators=[dimension_validator])
    link_to = models.URLField(max_length=255, verbose_name='Ссылка перехода',
                              help_text='Только абсолютная ссылка с http или https.',
                              validators=[safe_url_validator])
    date_from = models.DateField(default=timezone.now, verbose_name='Дата старта показа баннеров', help_text='')
    date_to = models.DateField(blank=True, null=True, verbose_name='Дата окончания показа баннеров',
                               help_text='Не заполняйте для показа без ограничения. В эту дату баннер ещё показывается.')
    date_days = models.IntegerField(default=254, verbose_name='Дни недели для показа',
                                    help_text='Вычисляется как сумма: Понедельник = 2, Вторник = 4, Среда = 8, '
                                              'Четверг = 16, Пятница = 32, Суббота = 64, Воскресенье = 128. '
                                              'Для всей недели = 254, Только выходные = 192, Только будни = 62')
    date_time_from = models.IntegerField(default=0, verbose_name='Час начала показа каждый указанный день',
                                         help_text='От 0 до 23 включительно.',
                                         validators=[MinValueValidator(0), MaxValueValidator(23)])
    date_time_to = models.IntegerField(default=24, verbose_name='Час окончания показа каждый указанный день',
                                       help_text='От 1 до 24 включительно; этот час уже не входит в показ.',
                                       validators=[MinValueValidator(1), MaxValueValidator(24)])
    priority = models.IntegerField(default=50, verbose_name='Приоритет показа от 1 до 100', help_text='Выше число — выше приоритет.',
                                   validators=[MinValueValidator(1), MaxValueValidator(100)])
    positions = models.ManyToManyField(Position, verbose_name='Места размещения баннера')
    active = models.BooleanField(default=True, verbose_name='Активность баннера')

    def __str__(self):
        return u'Баннер {}'.format(self.name)

    def __unicode__(self):
        return u'#{} {}'.format(self.id, self.name)

    @property
    def safe_width(self):
        return self._safe_dimension(self.width)

    @property
    def safe_height(self):
        return self._safe_dimension(self.height)

    @staticmethod
    def _safe_dimension(value):
        """Return a CSS dimension only when it also is safe for legacy rows."""
        if value and re.fullmatch(DIMENSION_PATTERN, value):
            return value
        return ''

    def clean(self):
        super().clean()
        errors = {}
        if self.date_to and self.date_from and self.date_to < self.date_from:
            errors['date_to'] = 'Дата окончания не может быть раньше даты начала.'
        if self.date_time_from is not None and self.date_time_to is not None:
            if self.date_time_to <= self.date_time_from:
                errors['date_time_to'] = 'Час окончания должен быть больше часа начала.'
        if not self.date_days & WEEKDAY_MASK:
            errors['date_days'] = 'Выберите хотя бы один день недели.'
        if errors:
            raise ValidationError(errors)

    class Meta:
        verbose_name = "Баннер"
        verbose_name_plural = "Баннеры"
