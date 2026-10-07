import json
import os
from pathlib import Path
import subprocess
import sys

import pytest


@pytest.mark.parametrize('module,default_hosts', [
    ('development', ['localhost', '127.0.0.1', '[::1]']),
    ('production', ['python.ru', '.python.ru', '127.0.0.1']),
])
@pytest.mark.parametrize('source', ['defaults', 'dotenv', 'environment', 'empty'])
def test_host_settings(tmp_path, module, default_hosts, source):
    dotenv = tmp_path / '.env'
    dotenv.write_text(
        'DATABASES_ENGINE=django.db.backends.postgresql\n'
        'DATABASES_NAME=test\n'
        'POSTGRES_API_USER=test\n'
        'POSTGRES_API_PASSWORD=test\n'
        'POSTGRES_API_HOST=localhost\n'
    )
    env = os.environ.copy()
    for name in ('ALLOWED_HOSTS', 'CSRF_TRUSTED_ORIGINS', 'DATABASE_URL'):
        env.pop(name, None)

    hosts = 'example.com, .example.com, localhost'
    origins = 'https://example.com, http://localhost:8080'
    if source in ('dotenv', 'environment', 'empty'):
        with dotenv.open('a') as file:
            file.write(f'ALLOWED_HOSTS={hosts}\nCSRF_TRUSTED_ORIGINS={origins}\n')
    if source == 'environment':
        hosts = 'override.example.com, 127.0.0.1'
        origins = 'https://override.example.com'
        env.update(ALLOWED_HOSTS=hosts, CSRF_TRUSTED_ORIGINS=origins)
    elif source == 'empty':
        env.update(ALLOWED_HOSTS='', CSRF_TRUSTED_ORIGINS='')

    # Fresh imports, isolated from Django's active settings and any local .env.
    result = subprocess.run(
        [
            sys.executable, '-c',
            'import decouple, importlib, json, sys; '
            'decouple.config = decouple.Config(decouple.RepositoryEnv(sys.argv[1])); '
            'settings = importlib.import_module(sys.argv[2]); '
            'print(json.dumps([settings.ALLOWED_HOSTS, settings.CSRF_TRUSTED_ORIGINS]))',
            str(dotenv), f'python_ru.settings.{module}',
        ],
        cwd=Path(__file__).resolve().parents[1],
        env=env, capture_output=True, text=True, check=True,
    )
    if source == 'defaults':
        expected = [default_hosts, []]
    elif source == 'empty':
        expected = [[], []]
    else:
        expected = [
            [host.strip() for host in hosts.split(',')],
            [origin.strip() for origin in origins.split(',')],
        ]
    assert json.loads(result.stdout) == expected
