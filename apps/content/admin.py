from django.contrib import admin

from apps.content.models import Link


@admin.register(Link)
class LinkAdmin(admin.ModelAdmin):
    list_display = ['name', 'section', 'order', 'url']
    list_filter = ['section']
    list_editable = ['order']

    fields = ['name', 'section', 'order', 'url', 'archive_notice']
    readonly_fields = ['archive_notice']
    search_fields = ['name', 'url']

    @admin.display(description='Архивный справочник')
    def archive_notice(self, obj):
        return 'Эти ссылки сохранены для архива и не выводятся в текущих разделах сайта.'
