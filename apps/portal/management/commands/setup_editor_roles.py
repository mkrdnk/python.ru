from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q


class Command(BaseCommand):
    help = 'Synchronize the managed Редакторы group; does not assign users.'

    @transaction.atomic
    def handle(self, *args, **options):
        group, _ = Group.objects.get_or_create(name='Редакторы')
        content = (Q(content_type__app_label='news', content_type__model='article')
                   | Q(content_type__app_label='events', content_type__model__in=['event', 'city'])
                   | Q(content_type__app_label='portal', content_type__model__in=[
                       'page', 'project', 'community', 'digest']))
        permissions = Permission.objects.filter(content).filter(
            Q(codename__startswith='view_') | Q(codename__startswith='add_') | Q(codename__startswith='change_'))
        proposals = Permission.objects.filter(content_type__app_label='portal',
                                             codename__in=['view_contribution', 'change_contribution'])
        group.permissions.set(permissions | proposals)
        self.stdout.write('Группа Редакторы настроена. Назначьте её staff-пользователям в админке.')
