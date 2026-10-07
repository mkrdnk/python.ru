from datetime import timedelta

from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Count
from django.http import Http404, HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils import timezone
from django.utils.html import format_html

from apps.portal.models import Community, Contribution, Delivery, Digest, DigestWorker, Page, Project, Subscriber
from apps.portal.delivery import enqueue, resolve_delivery
from python_ru.admin_mixins import ContributionTargetMixin, PreviewAdminMixin, PublishAdminMixin


class DirectoryAdmin(ContributionTargetMixin, PreviewAdminMixin, PublishAdminMixin, admin.ModelAdmin):
    list_editable = ['is_active', 'position']
    search_fields = ['name', 'description']
    preview_template = 'admin/directory_preview.html'


@admin.register(Project)
class ProjectAdmin(DirectoryAdmin):
    list_display = ['name', 'category', 'is_active', 'position']
    list_filter = ['is_active', 'category']
    fieldsets = [('Проект', {'fields': ['name', 'description', 'url', 'category']}),
                 ('Публикация', {'fields': ['is_active', 'position', 'stars']})]


@admin.register(Community)
class CommunityAdmin(DirectoryAdmin):
    list_display = ['name', 'city', 'is_active', 'position']
    list_filter = ['is_active', 'city']
    search_fields = ['name', 'city', 'description']
    fieldsets = [('Сообщество', {'fields': ['name', 'description', 'url', 'city']}),
                 ('Публикация', {'fields': ['is_active', 'position', 'members']})]


@admin.register(Page)
class PageAdmin(PreviewAdminMixin, PublishAdminMixin, admin.ModelAdmin):
    list_display = ['title', 'slug', 'is_active']
    search_fields = ['title', 'body']
    list_filter = ['is_active']
    prepopulated_fields = {'slug': ['title']}
    fields = ['title', 'slug', 'body', 'is_active']
    preview_template = 'portal/page.html'


@admin.register(Contribution)
class ContributionAdmin(admin.ModelAdmin):
    change_form_template = 'admin/editorial_change_form.html'
    list_display = ['title', 'kind', 'created_at', 'status', 'assignee']
    list_filter = ['kind', 'status', 'assignee']
    list_select_related = ['assignee']
    search_fields = ['title', 'name', 'email']
    readonly_fields = ['kind', 'title', 'name', 'email', 'url', 'description', 'created_at', 'target_link']
    fields = readonly_fields + ['status', 'assignee', 'internal_note']

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        # An editor updating notes must not overwrite a concurrently created link.
        with transaction.atomic():
            if object_id and request.method == 'POST':
                Contribution.objects.select_for_update().filter(pk=object_id).first()
            return super().changeform_view(request, object_id, form_url, extra_context)

    def has_add_permission(self, request):
        return False

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'assignee':
            kwargs['queryset'] = db_field.remote_field.model.objects.filter(is_active=True, is_staff=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    @admin.display(description='Созданная запись')
    def target_link(self, obj):
        if not obj.target:
            return 'Черновик ещё не создан'
        target = obj.target
        return format_html('<a href="{}">{}</a>', reverse(
            f'admin:{target._meta.app_label}_{target._meta.model_name}_change', args=[target.pk]), target)

    def render_change_form(self, request, context, *args, **kwargs):
        obj = context.get('original')
        if obj and not obj.target and self.has_change_permission(request, obj):
            model = obj._meta.get_field(obj.kind).remote_field.model
            if self.admin_site._registry[model].has_add_permission(request):
                context['editorial_links'] = [{'title': 'Создать черновик', 'url': reverse(
                    f'admin:{model._meta.app_label}_{model._meta.model_name}_add') + f'?contribution={obj.pk}'}]
        return super().render_change_form(request, context, *args, **kwargs)


@admin.register(Subscriber)
class SubscriberAdmin(admin.ModelAdmin):
    list_display = ['email', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['email']
    readonly_fields = ['token', 'created_at']


@admin.register(Digest)
class DigestAdmin(PreviewAdminMixin, admin.ModelAdmin):
    list_display = ['subject', 'state', 'delivery_progress', 'created_at', 'sent_at']
    list_filter = ['state']
    search_fields = ['subject']
    readonly_fields = ['state', 'created_at', 'queued_at', 'sent_at', 'delivery_progress', 'worker_status']
    fields = ['subject', 'body', *readonly_fields]
    preview_template = 'admin/digest_preview.html'

    def get_readonly_fields(self, request, obj=None):
        return self.readonly_fields + (['subject', 'body'] if obj and obj.state != 'draft' else [])

    def has_delete_permission(self, request, obj=None):
        return super().has_delete_permission(request, obj) and (obj is None or obj.state == 'draft')

    def get_actions(self, request):
        actions = super().get_actions(request)
        actions.pop('delete_selected', None)
        return actions

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        # Serialize edits with queue submission so the frozen contents cannot change in flight.
        with transaction.atomic():
            if object_id and request.method == 'POST':
                Digest.objects.select_for_update().filter(pk=object_id).first()
            return super().changeform_view(request, object_id, form_url, extra_context)

    @admin.display(description='Доставки')
    def delivery_progress(self, obj):
        if not obj.pk:
            return '—'
        counts = obj.delivery_set.values('state').annotate(total=Count('pk'))
        labels = dict(Delivery.STATES)
        text = ', '.join(f'{labels[row["state"]]}: {row["total"]}' for row in counts) or 'Нет доставок'
        return text

    @admin.display(description='Обработчик рассылки')
    def worker_status(self, obj):
        alive = DigestWorker.objects.filter(heartbeat__gte=timezone.now() - timedelta(minutes=2)).exists()
        return 'Работает' if alive else 'Нет активного обработчика. Отправка будет ожидать его запуска.'

    def get_urls(self):
        return [path('<int:object_id>/actions/<str:operation>/', self.admin_site.admin_view(self.operation_view),
                     name='portal_digest_operation')] + super().get_urls()

    def render_change_form(self, request, context, *args, **kwargs):
        obj = context.get('original')
        if obj:
            links = []
            if request.user.has_perm('portal.view_delivery'):
                links.append({'title': 'Доставки выпуска', 'url': reverse('admin:portal_delivery_changelist') + f'?digest__id__exact={obj.pk}'})
            if self.has_add_permission(request):
                links.append({'title': 'Копировать в черновик', 'url': reverse('admin:portal_digest_operation', args=[obj.pk, 'copy'])})
            if obj.state == 'draft' and self.has_change_permission(request, obj) and request.user.has_perm('portal.send_digest'):
                links.append({'title': 'Отправить выпуск', 'url': reverse('admin:portal_digest_operation', args=[obj.pk, 'send'])})
            context['editorial_links'] = links
        return super().render_change_form(request, context, *args, **kwargs)

    def operation_view(self, request, object_id, operation):
        if operation not in ('send', 'copy'):
            raise Http404
        obj = self.get_object(request, object_id)
        if obj is None:
            raise Http404
        if not self.has_view_or_change_permission(request, obj):
            raise PermissionDenied
        if operation == 'send' and not (self.has_change_permission(request, obj) and request.user.has_perm('portal.send_digest')):
            raise PermissionDenied
        if operation == 'copy' and not self.has_add_permission(request):
            raise PermissionDenied
        if request.method == 'POST':
            if operation == 'copy':
                obj = Digest.objects.create(subject=obj.subject, body=obj.body)
                self.log_addition(request, obj, 'Скопирован в черновик')
            else:
                try:
                    obj = enqueue(obj.pk)
                    self.log_change(request, obj, 'Подтверждена отправка выпуска')
                    self.message_user(request, 'Выпуск поставлен в очередь; повторная постановка не создаёт доставок.')
                except ValueError as exc:
                    self.message_user(request, str(exc), level=messages.ERROR)
            return HttpResponseRedirect(reverse('admin:portal_digest_change', args=[obj.pk]))
        return TemplateResponse(request, 'admin/confirm_editorial.html', {
            **self.admin_site.each_context(request), 'title': obj.subject,
            'explanation': (f'Зафиксировать выпуск и отправить {Subscriber.objects.filter(is_active=True).count()} подписчикам? '
                            'Отправка выполняется фоновым обработчиком.' if operation == 'send' else 'Создать новый редактируемый выпуск?'),
            'button': 'Подтвердить отправку' if operation == 'send' else 'Создать черновик',
            'preview_url': reverse('admin:portal_digest_preview', args=[obj.pk]),
        })


@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    list_display = ['email', 'digest', 'state', 'attempted_at', 'sent_at']
    list_filter = ['state', 'digest']
    search_fields = ['email', 'digest__subject']
    list_select_related = ['digest']
    readonly_fields = ['digest', 'subscriber', 'email', 'state', 'attempted_at', 'sent_at', 'error']
    fields = readonly_fields
    change_form_template = 'admin/editorial_change_form.html'
    actions = None

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_urls(self):
        return [path('<int:object_id>/resolve/<str:decision>/', self.admin_site.admin_view(self.resolve_view),
                     name='portal_delivery_resolve')] + super().get_urls()

    def render_change_form(self, request, context, *args, **kwargs):
        obj = context.get('original')
        if obj and obj.state in ('failed', 'uncertain') and request.user.has_perm('portal.send_digest') and self.has_change_permission(request, obj):
            context['editorial_links'] = [
                {'title': title, 'url': reverse('admin:portal_delivery_resolve', args=[obj.pk, decision])}
                for decision, title in [('retry', 'Повторить доставку'), ('sent', 'Подтвердить доставку')]]
        return super().render_change_form(request, context, *args, **kwargs)

    def resolve_view(self, request, object_id, decision):
        obj = self.get_object(request, object_id)
        if obj is None or decision not in ('retry', 'sent'):
            raise Http404
        if not self.has_change_permission(request, obj) or not request.user.has_perm('portal.send_digest'):
            raise PermissionDenied
        if request.method == 'POST':
            try:
                resolve_delivery(obj.pk, decision)
                self.log_change(request, obj, 'Повтор доставки' if decision == 'retry' else 'Доставка подтверждена вручную')
            except ValueError as exc:
                self.message_user(request, str(exc), level=messages.ERROR)
            return HttpResponseRedirect(reverse('admin:portal_delivery_change', args=[obj.pk]))
        return TemplateResponse(request, 'admin/confirm_editorial.html', {
            **self.admin_site.each_context(request), 'title': obj.email,
            'explanation': 'Проверьте журнал SMTP-провайдера. Повтор неизвестной доставки может отправить письмо ещё раз.',
            'button': 'Повторить доставку' if decision == 'retry' else 'Считать доставленным',
        })
