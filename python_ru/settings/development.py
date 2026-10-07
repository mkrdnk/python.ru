from __future__ import absolute_import, unicode_literals

from .base import *

DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '[::1]']

DATABASES = {
    'default': {
        'ENGINE': config('DATABASES_ENGINE', default='django.db.backends.sqlite3'),
        'NAME': os.path.join(BASE_DIR, config('DATABASES_NAME', default='../../db.sqlite3', cast=str)),
    }
}
db_from_env = dj_database_url.config(conn_max_age=500)
DATABASES['default'].update(db_from_env)
