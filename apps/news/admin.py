from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html

from apps.news.models import Article
from python_ru.admin_mixins import ContributionTargetMixin, PreviewAdminMixin, PublishAdminMixin


class HasImage(admin.SimpleListFilter):
    title = 'Есть картинка'
    parameter_name = 'image'

    def lookups(self, request, model_admin):
        return [('yes', 'Есть'), ('no', 'Нет')]

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.exclude(image='')
        if self.value() in ('no', 'not'):
            return queryset.filter(image='')
        return queryset


@admin.register(Article)
class ArticleAdmin(ContributionTargetMixin, PreviewAdminMixin, PublishAdminMixin, admin.ModelAdmin):
    list_display = ['name', 'kind', 'author', 'is_active', 'published_at', 'has_image']
    search_fields = ['name', 'author', 'tags']
    list_filter = ['kind', 'is_active', HasImage]
    date_hierarchy = 'published_at'
    preview_template = 'post.html'
    preview_context_name = 'post'
    readonly_fields = ['image_preview']
    fieldsets = [
        ('Материал', {'fields': ['name', 'kind', 'author', 'description', 'text', 'image', 'image_preview']}),
        ('Публикация', {'fields': ['tags', 'reading_minutes', 'published_at', 'is_active', 'url']}),
    ]

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if 'url' in form.base_fields:
            form.base_fields['url'].label = 'Ссылка на оригинал'
            form.base_fields['url'].help_text = 'Необязательно. Новые материалы открываются на Python.ru.'
        return form

    def get_changeform_initial_data(self, request):
        return {'published_at': timezone.now(), **super().get_changeform_initial_data(request)}

    def save_model(self, request, obj, form, change):
        if not change:
            obj.is_our, obj.language, obj.source = True, 'ru', 'python.ru'
        super().save_model(request, obj, form, change)

    @admin.display(boolean=True, description='Картинка')
    def has_image(self, obj):
        return bool(obj.image)

    @admin.display(description='Обложка')
    def image_preview(self, obj):
        if obj and obj.image:
            return format_html('<img src="{}" alt="" style="max-width:320px;max-height:180px">', obj.image.url)
        return '—'
