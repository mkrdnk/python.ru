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

Environment settings
~~~~~~~~~~~~~~~~~~~~

Copy ``.env.example`` to ``.env`` in the project root for local configuration.
Settings read through python-decouple use process environment variables first,
then ``.env``. For example::

    DEBUG=True
    ALLOWED_HOSTS=localhost,127.0.0.1,dev.example.com
    CSRF_TRUSTED_ORIGINS=https://dev.example.com
    SITE_URL=https://dev.example.com

``ALLOWED_HOSTS`` is a comma-separated list of hostnames without schemes, ports
or paths. ``CSRF_TRUSTED_ORIGINS`` is a comma-separated list of trusted origins
including their scheme and non-standard port, if any; leave it empty unless
cross-origin unsafe requests need to be allowed. ``SITE_URL`` is the public
base URL used for email links. Use ``DEBUG=False`` and a unique
``DJANGO_SECRET_KEY`` in production; never commit real secrets.

``DJANGO_SETTINGS_MODULE`` must be supplied in the process environment to
select a settings module; putting it in ``.env`` alone does not select one.
``manage.py`` defaults to development, while WSGI defaults to production.
Likewise, ``DATABASE_URL`` is read from the process environment, not ``.env``.
See ``.env.example`` for the separate production database variables.

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

Compose also accepts ``DJANGO_SECRET_KEY``, ``DEBUG``, ``ALLOWED_HOSTS``,
``CSRF_TRUSTED_ORIGINS`` and ``SITE_URL`` from the shell or root ``.env`` file.
With no overrides, ``SITE_URL`` follows ``WEB_PORT``. If copying ``.env.example``,
adjust its ``SITE_URL`` to the chosen Compose port (8080 by default).
Recreate the web container after changing environment values::

    docker compose up -d

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

Banners
~~~~~~~

Run ``python manage.py migrate`` before using the updated banner admin. The
migration creates the supported placements and preserves existing banners and
their placement assignments.

In ``/admin/banners/banner/``, add or edit a banner:

1. Enter a descriptive name (also used as image alternative text), upload an
   image and enter the destination URL.
2. Select one or more placements:

   * ``Под шапкой`` (``top``): below the header on public pages.
   * ``В сайдбаре главной страницы`` (``sidebar``): above the events in the home page sidebar.
     On narrow screens this column moves below the news list.
   * ``После статьи`` (``article_end``): after the body and source link on an
     article page.
   * ``Перед подвалом`` (``bottom``): before the footer on public pages.

3. Set the start date, optionally an end date, and the weekdays/hours for display.
   Both dates are inclusive; the ending hour is exclusive (``0–24`` means all
   day). Scheduling uses the site's ``TIME_ZONE`` (``Europe/Moscow`` by default).
4. Enable the banner and save. Disable it to stop showing it without deleting it.

Each placement displays one eligible banner: the highest priority wins, and
equal priorities use the lowest banner ID. There is no random rotation.
The same banner can appear in multiple selected placements on one page.
An empty placement adds no markup or reserved space.

Image dimensions can be left blank for the natural size, constrained to the
available page width. Optional dimensions accept values such as ``720px`` or
``100%``; width controls the requested size and height limits the image height.
Images keep their proportions on mobile. Uploaded images are served from
``MEDIA_URL``; production must serve ``MEDIA_ROOT`` as usual.

Legacy placement records are retained, but arbitrary placement codes do not
create new areas in the site layout. Reassign old banners to supported placements
in the admin to show them. Legacy SWF data is retained but is not rendered;
upload an image instead. Adding an entirely new placement requires a template
change, not just a new database record.

To rebuild the exact design stylesheet after changing the source::

    cd redisign
    pnpm install --frozen-lockfile
    cd ..
    node scripts/build-design.mjs

The build script leaves the reference source untouched and replaces only
``assets/css/redisign.css``. The home page retains the reference's six opening
stories and explicit load-more button, keeping the lower sections reachable.
The material archive retains automatic pagination.
