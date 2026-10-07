from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import Http404, HttpResponseRedirect
from django.template.loader import render_to_string
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import escape


class PreviewAdminMixin:
    change_form_template = 'admin/editorial_change_form.html'
    preview_template = None
    preview_context_name = 'object'

    def get_urls(self):
        return [path('<path:object_id>/preview/', self.admin_site.admin_view(self.preview_view),
                     name=f'{self.opts.app_label}_{self.opts.model_name}_preview')] + super().get_urls()

    def preview_view(self, request, object_id):
        obj = self.get_object(request, object_id)
        if obj is None:
            raise Http404
        if not self.has_view_or_change_permission(request, obj):
            raise PermissionDenied
        context = {self.preview_context_name: obj}
        if self.opts.model_name in ('project', 'community'):
            context.update(section=self.opts.model_name, entries=[obj])
        html = render_to_string(self.preview_template, context, request=request)
        return TemplateResponse(request, 'admin/preview.html', {
            **self.admin_site.each_context(request), 'title': 'Предпросмотр сохранённой версии',
            'preview_html': html, 'opts': self.opts,
        })

    def render_change_form(self, request, context, *args, **kwargs):
        obj = context.get('original')
        if obj and self.has_view_or_change_permission(request, obj):
            context['preview_url'] = reverse(
                f'admin:{self.opts.app_label}_{self.opts.model_name}_preview', args=[obj.pk])
        return super().render_change_form(request, context, *args, **kwargs)


class PublishAdminMixin:
    actions = ['publish', 'unpublish']

    def set_publication(self, request, queryset, active):
        with transaction.atomic():
            count = 0
            for obj in queryset.select_for_update():
                if not self.has_change_permission(request, obj):
                    raise PermissionDenied
                obj.is_active = active
                obj.save(update_fields=['is_active'])
                self.log_change(request, obj, 'Опубликовано' if active else 'Снято с публикации')
                count += 1
        self.message_user(request, f'Изменено записей: {count}.')

    @admin.action(description='Опубликовать', permissions=['change'])
    def publish(self, request, queryset):
        self.set_publication(request, queryset, True)

    @admin.action(description='Снять с публикации', permissions=['change'])
    def unpublish(self, request, queryset):
        self.set_publication(request, queryset, False)


class ContributionTargetMixin:
    """Hold the proposal lock through ModelAdmin's complete add transaction."""
    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        proposal_id = request.GET.get('contribution')
        if object_id is not None or not proposal_id:
            return super().changeform_view(request, object_id, form_url, extra_context)
        from apps.portal.models import Contribution
        with transaction.atomic():
            try:
                proposal = Contribution.objects.select_for_update().get(pk=proposal_id)
            except (Contribution.DoesNotExist, ValueError):
                raise Http404
            ma = self.admin_site._registry[Contribution]
            if not ma.has_change_permission(request, proposal) or not self.has_add_permission(request):
                raise PermissionDenied
            if proposal.kind != self.opts.model_name:
                raise PermissionDenied
            if proposal.target:
                target = proposal.target
                return HttpResponseRedirect(reverse(
                    f'admin:{target._meta.app_label}_{target._meta.model_name}_change', args=[target.pk]))
            request.editorial_proposal = proposal
            return super().changeform_view(request, object_id, form_url, extra_context)

    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)
        proposal = getattr(request, 'editorial_proposal', None)
        if proposal:
            initial.update(name=proposal.title, url=proposal.url, is_active=False)
            if proposal.kind == 'article':
                initial.update(author=proposal.name, description=str(escape(proposal.description)))
            elif proposal.kind == 'event':
                initial['description_html'] = str(escape(proposal.description)).replace('\n', '<br>')
            else:
                initial['description'] = proposal.description
        return initial

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        proposal = getattr(request, 'editorial_proposal', None)
        if proposal and not change:
            setattr(proposal, proposal.kind, form.instance)
            proposal.status = 'review'
            proposal.assignee = proposal.assignee or request.user
            proposal.save(update_fields=[proposal.kind, 'status', 'assignee'])
            self.admin_site._registry[type(proposal)].log_change(request, proposal, 'Создан черновик')
