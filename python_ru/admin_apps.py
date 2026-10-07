from django.contrib.admin.apps import AdminConfig


class EditorialAdminConfig(AdminConfig):
    default_site = 'python_ru.admin.EditorialAdminSite'
