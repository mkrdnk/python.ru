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
* Events use a simple calendar: name, city, date, rich description, URL and publication status.
  Talks, speakers, employers, registration and broadcast settings have been retired.
* The Portal section manages projects, communities, informational pages,
  private reader submissions, subscribers and digest issues.
* Projects and communities are drafts by default. Star/member counts are
  optional editorial values, not live API counters.
* Initial informational pages and the Moscow Python link are created by a
  migration. Reference mock articles, events and counts are not imported.

Editorial administration
~~~~~~~~~~~~~~~~~~~~~~~~

The Django admin is grouped by editorial tasks rather than application names.
Articles expose only content and publication fields. Source, language, imported
category, external ID and legacy feature flags are retained in the database but
hidden from every admin form and list. New manually created articles open on
Python.ru; their optional original URL is a source link. Existing articles and
the Python Digest importer retain their previous link behaviour.

After deploying, synchronize the managed editor group::

    python manage.py setup_editor_roles

Assign ``Редакторы`` to staff users in the user admin. Re-running this command
restores the group's documented permission set; use another group for custom
permissions. It does not assign users automatically. Editors may create, edit
and publish content and prepare digests. They cannot delete content, manage
users, subscribers or advertisements, or send digests. Superusers retain full
access; delegated administrators need the relevant model permissions and
``portal.send_digest`` to send or resolve deliveries.

Use **Предпросмотр** on a saved record to inspect its current saved version.
Previews require staff access and model view/change permission, are not cached,
and render in a sandboxed frame. Public URLs still hide unpublished content.

Reader proposals retain the original submission as read-only. Assign an editor,
add internal notes, and choose **Создать черновик**. Fill in missing required
fields and save; this creates one linked draft and marks the proposal as under
review. Cancelling the form does not create anything. Repeated requests open
the existing draft. Mark the proposal processed explicitly when finished.

Meetup retirement and deployment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Back up the database and media before migrating.** The new migrations delete
talks, speakers, employers and event registration/broadcast/place-and-time fields.
Rollback does not restore deleted data; restoring the backup is required.
Event IDs, names, cities, dates, descriptions and external URLs remain intact.
Uploaded avatar files are not removed automatically.

``apps.meetups`` remains installed only as a migration compatibility shell; it
has no runtime models or admin screens. Existing unique, published meetup slugs
redirect permanently to ``/events/ID/``. Missing or ambiguous slugs return 410;
``/junior/`` uses the same rule for the old ``junior`` slug. Events with an
external URL link to that URL; other events use their internal calendar page.

Deployment sequence: stop web writes and old mail senders, back up data, deploy
the new code, run ``migrate``, ``setup_editor_roles`` and ``collectstatic``, then
start the web service and new digest worker. Check public pages, editor access
and the worker heartbeat before enabling sends. The production Compose file is
maintained outside this repository and must be updated separately.

Digest queue
~~~~~~~~~~~~

Subscription forms store addresses; each delivered issue contains an unsubscribe
link. No email is sent by signup, migrations, ordinary saves or preview.
Editors prepare issues. An administrator chooses **Отправить выпуск**, reviews
the saved preview and recipient count, and confirms. This freezes the content
and active recipient list, then queues deliveries in PostgreSQL. New subscribers
are not added later; subscribers who unsubscribe before sending are skipped.
Queued issues are read-only; **Копировать в черновик** creates an editable issue.

Configure ``EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend``,
``EMAIL_HOST``, ``EMAIL_PORT``, ``EMAIL_HOST_USER``, ``EMAIL_HOST_PASSWORD``,
``EMAIL_USE_TLS``, ``DEFAULT_FROM_EMAIL`` and ``SITE_URL``. SMTP calls use a
30-second timeout. Run the worker as a separate supervised process, sharing the
web application's database and mail configuration::

    python manage.py digest_worker
    python manage.py check_digest_worker

The Docker image supports ``runworker`` as its command. Locally, after configuring
SMTP in the shell or ``.env``, start the optional worker profile::

    docker compose --profile mail up --build -d

The worker depends on the web health check, so migrations complete first.
Default Compose uses a console backend and does not start a worker. The worker
refuses non-SMTP backends. Do not configure real recipient data for local tests.
No Redis, Celery or periodic mail schedule is required.

The CLI uses the same queue::

    python manage.py send_digest ISSUE_ID          # show audience; send nothing
    python manage.py send_digest ISSUE_ID --send   # freeze and queue; does not send inline
    python manage.py digest_worker --once          # process available jobs and exit

Repeated enqueue requests do not add recipients or repeat successful deliveries.
Multiple workers reserve deliveries using PostgreSQL row locks. The admin shows
progress, errors and whether a worker checked in during the last two minutes.
Monitor ``check_digest_worker`` and service logs; pending jobs remain queued
when workers are stopped.

After a worker interruption, reservations older than five minutes become
**Результат неизвестен**. SMTP exceptions with an uncertain outcome also require
review. Consult the SMTP provider's logs, then use **Подтвердить доставку** or
**Повторить доставку** on that delivery. These actions require send and delivery
change permissions, explicit POST confirmation, and are recorded in the admin
log. SMTP cannot guarantee exactly-once delivery across process crashes.
Historical successful deliveries are preserved; previously sent or partially
sent issues are closed rather than automatically resumed.

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
