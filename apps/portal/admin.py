from django.contrib import admin
from apps.portal.models import Community, Contribution, Digest, Page, Project, Subscriber


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'is_active', 'position']
    list_editable = ['is_active', 'position']
    list_filter = ['is_active', 'category']
    search_fields = ['name', 'description']


@admin.register(Community)
class CommunityAdmin(admin.ModelAdmin):
    list_display = ['name', 'city', 'is_active', 'position']
    list_editable = ['is_active', 'position']
    list_filter = ['is_active', 'city']
    search_fields = ['name', 'city']


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'is_active']
    prepopulated_fields = {'slug': ['title']}


@admin.register(Contribution)
class ContributionAdmin(admin.ModelAdmin):
    list_display = ['title', 'kind', 'created_at', 'status']
    list_filter = ['kind', 'status']
    search_fields = ['title', 'name', 'email']
    readonly_fields = ['created_at']


@admin.register(Subscriber)
class SubscriberAdmin(admin.ModelAdmin):
    list_display = ['email', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['email']
    readonly_fields = ['token', 'created_at']


@admin.register(Digest)
class DigestAdmin(admin.ModelAdmin):
    list_display = ['subject', 'created_at', 'sent_at']
    readonly_fields = ['created_at', 'sent_at']
