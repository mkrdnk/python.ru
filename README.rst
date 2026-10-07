Contributing
============

Requires Python 3.13. Docker uses the same Python version. Production PostgreSQL
must be version 14 or newer for Django 5.2.

::

    git clone git@github.com:moscowpython/python.ru.git
    cd python.ru
    python3.13 -m venv .venv
    source .venv/bin/activate
    python -m pip install -r requirements-dev.txt
    python manage.py migrate
    python manage.py loaddata fixtures/development.json
    python manage.py runserver
    python manage.py createsuperuser

Local test environment with Docker Compose
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Start Django and PostgreSQL without installing Python locally::

    docker compose up --build -d --wait
    docker compose exec web python manage.py createsuperuser

Open http://localhost:8080/ (admin: http://localhost:8080/admin/).
To choose another port, use ``WEB_PORT=8081 docker compose up --build -d --wait``.
No .env file is required. This configuration is for local testing: DEBUG is on,
credentials are disposable local defaults, and Django serves static files and
uploads directly. Emails go to container logs.

Code is mounted from the current checkout; Django reloads Python changes.
Rebuild the image after changing requirements. Migrations run automatically
before the web server starts. The database and uploads live in named volumes
and survive container recreation. The database port is not exposed to the host.

Useful commands::

    docker compose logs -f web
    docker compose exec web python manage.py shell
    docker compose down

To load the optional development fixture and its images::

    docker compose exec web python manage.py loaddata fixtures/development.json
    docker compose exec web sh -c 'cp -R fixtures/media/. /opt/media/'

``docker compose down --volumes`` resets this environment, deleting its database
and uploaded files. A different project name (``docker compose -p pythonru-test``)
creates separate volumes; use the same name for subsequent commands.

Dependency updates
~~~~~~~~~~~~~~~~~~

``requirements.in`` declares runtime dependencies; ``requirements-dev.in`` adds
test tooling. The committed ``.txt`` files pin the complete resolved dependency
sets. They replace the outdated, conflicting Pipfile/Pipfile.lock. Production
installs only ``requirements.txt`` (including Gunicorn).

To update and verify using uv::

    uv pip compile requirements.in --python-version 3.13 --universal --upgrade -o requirements.txt
    uv pip compile requirements-dev.in --python-version 3.13 --universal -c requirements.txt --upgrade -o requirements-dev.txt
    python -m pip install -r requirements-dev.txt
    python manage.py check
    python manage.py makemigrations --check --dry-run
    pytest

The editor now uses CKEditor 5. Run migrations and collectstatic after upgrading.
Existing article HTML and image URLs are retained. A database-only legacy field
keeps old migrations runnable without installing CKEditor 4. Back up the database
and media before upgrading a deployed installation.

The Python Digest importer still reads RSS and the date API. Its optional
``READABILITY_PARSER_KEY`` integration was removed with the obsolete Readability
API client; descriptions and images now come from the feed itself.

The ``redisign/`` build requires Node.js 22.12+ and pnpm 11.19.0. Install reproducibly with
``pnpm --dir redisign install --frozen-lockfile``; update its lock with
``pnpm --dir redisign update`` and rebuild via ``node scripts/build-design.mjs``.

Updating development fixture
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
::

    $ python manage.py dumpdata --exclude=auth --exclude=sessions --exclude=contenttypes --exclude=admin --indent 4 > fixtures/development.json
    $ cp -R media/ fixtures/media/

    # Commit fixtures, keeping their size reasonable

Tests
=====
::

    $ pip install tox
    $ tox

Portal design and content
~~~~~~~~~~~~~~~~~~~~~~~~~

The public templates use the design supplied in ``redisign/``. Its original
React prototype is kept as a reference; Django renders live content directly,
so production does not require a Node.js build. The original design stylesheet is compiled into ``assets/css/redisign.css``;
Django page extensions are in ``assets/css/site.css`` and theme/search/menu behaviour is in ``assets/js/site.js``.

Apply the migrations before serving the updated templates::

    python manage.py migrate
    python manage.py collectstatic --noinput

In ``/admin/``:

* Articles support type (including notes/interviews/translations), author,
  comma-separated tags and optional reading time. Only active items are public.
* Events retain their existing editor and talks. Internal event pages and
  external event URLs are both supported.
* The Portal section manages projects, communities, informational pages,
  private reader submissions, subscribers and digest issues.
* Projects and communities are drafts by default. Star/member counts are
  optional editorial values, not live API counters.
* Initial informational pages and the Moscow Python link are created by a
  migration. Reference mock articles, events and counts are not imported.

Subscription forms store addresses and unsubscribe links appear in each digest.
No emails are sent by migrations, signup or admin saves. To deliver an issue,
configure ``EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend``,
``EMAIL_HOST``, ``EMAIL_PORT``, ``EMAIL_HOST_USER``, ``EMAIL_HOST_PASSWORD``,
``EMAIL_USE_TLS``, ``DEFAULT_FROM_EMAIL`` and ``SITE_URL``. Then::

    python manage.py send_digest ISSUE_ID          # preview recipient count
    python manage.py send_digest ISSUE_ID --send   # send the approved issue

Run one sender at a time. Successful deliveries are recorded so ordinary retries
skip them; as with SMTP generally, a process crash after the server accepts a
message but before the database commit can require manual delivery reconciliation.
The command does not schedule recurring sends. Store SMTP credentials outside git.

To rebuild the exact design stylesheet after changing the source::

    cd redisign
    pnpm install --frozen-lockfile
    cd ..
    node scripts/build-design.mjs

The build script leaves the reference source untouched and replaces only
``assets/css/redisign.css``. The home page retains the reference's six opening
stories and explicit load-more button, keeping the lower sections reachable.
The material archive retains automatic pagination.
