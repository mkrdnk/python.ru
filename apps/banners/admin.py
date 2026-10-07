from django.contrib import admin
from django import forms
from django.utils.html import format_html

from apps.banners.models import (
    Banner,
    Position,
    SUPPORTED_SLOT_TAGS,
    WEEKDAY_CHOICES,
)


class BannerAdminForm(forms.ModelForm):
    file_img = forms.ImageField(
        label='Изображение',
        help_text='Загрузите изображение PNG, JPEG, GIF или WebP.',
    )
    weekdays = forms.MultipleChoiceField(
        choices=WEEKDAY_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        label='Дни недели для показа',
        help_text='Баннер будет показан в отмеченные дни.',
    )

    class Meta:
        model = Banner
        fields = (
            'name', 'file_img', 'link_to', 'positions', 'width', 'height',
            'date_from', 'date_to', 'date_time_from', 'date_time_to',
            'priority', 'active',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['file_img'].required = True
        self.fields['positions'].queryset = Position.objects.filter(
            tag__in=SUPPORTED_SLOT_TAGS,
        ).order_by('name', 'pk')
        self.fields['positions'].help_text = (
            'Доступны только места, которые выводятся на сайте. '
            'Старые места с другими тегами сохранены, но не отображаются.'
        )
        mask = self.instance.date_days if self.instance.pk else Banner._meta.get_field('date_days').default
        self.initial['weekdays'] = [
            str(value) for value, _ in WEEKDAY_CHOICES if mask & value
        ]

    def clean(self):
        cleaned_data = super().clean()
        weekdays = cleaned_data.get('weekdays')
        if not weekdays:
            self.add_error('weekdays', 'Выберите хотя бы один день недели.')
        else:
            self.instance.date_days = sum(int(value) for value in weekdays)
        return cleaned_data

    def save(self, commit=True):
        self.instance.date_days = sum(
            int(value) for value in self.cleaned_data.get('weekdays', ())
        )
        return super().save(commit=commit)


class BannerAdmin(admin.ModelAdmin):
    form = BannerAdminForm
    list_display = (
        'name', 'placement_list', 'date_from', 'date_to', 'priority', 'active',
    )
    list_filter = ('active', 'positions')
    search_fields = ('name', 'link_to')
    filter_horizontal = ('positions',)
    fieldsets = (
        ('Баннер', {
            'fields': ('name', ('file_img', 'image_preview'), 'link_to', 'positions', 'active'),
        }),
        ('Расписание', {
            'fields': (
                ('date_from', 'date_to'), 'weekdays',
                ('date_time_from', 'date_time_to'), 'priority',
            ),
        }),
        ('Размер', {
            'fields': (('width', 'height'),),
        }),
    )
    readonly_fields = ('image_preview',)

    @admin.display(description='Места размещения')
    def placement_list(self, obj):
        return ', '.join(position.name for position in obj.positions.all())

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('positions')

    @admin.display(description='Предпросмотр')
    def image_preview(self, obj):
        if not obj.file_img:
            return '—'
        return format_html(
            '<img src="{}" alt="{}" style="max-width: 320px; max-height: 160px;">',
            obj.file_img.url,
            obj.name,
        )


class PositionAdmin(admin.ModelAdmin):
    list_display = ('name', 'tag', 'is_rendered')
    search_fields = ('name', 'tag')

    @admin.display(boolean=True, description='Отображается на сайте')
    def is_rendered(self, obj):
        return obj.is_supported_slot


admin.site.register(Banner, BannerAdmin)
admin.site.register(Position, PositionAdmin)
