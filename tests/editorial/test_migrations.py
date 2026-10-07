import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.utils import timezone


@pytest.mark.django_db(transaction=True)
def test_retirement_and_queue_migrations_preserve_remaining_content():
    executor = MigrationExecutor(connection)
    latest = executor.loader.graph.leaf_nodes()
    before = [('portal', '0003_alter_digest_body_alter_page_body'),
              ('events', '0005_event_place_and_time_html'), ('meetups', '0002_auto_20180225_2107'),
              ('news', '0009_alter_article_text')]
    try:
        executor.migrate(before)
        old = executor.loader.project_state(before).apps
        city = old.get_model('events', 'City').objects.create(name='Москва')
        event = old.get_model('events', 'Event').objects.create(
            city=city, name='Legacy event', slug='legacy', has_page_on_site=True,
            description_html='<p>Описание</p>', register_url='https://example.org/register')
        employer = old.get_model('meetups', 'Employer').objects.create(name='Company')
        speaker = old.get_model('meetups', 'Speaker').objects.create(
            first_name='Speaker', last_name='Name', employer=employer, avatar='old/avatar.png')
        old.get_model('meetups', 'Talk').objects.create(event=event, speaker=speaker, title='Talk', description='Text')
        subscriber = old.get_model('portal', 'Subscriber').objects.create(email='legacy@example.org')
        digest = old.get_model('portal', 'Digest').objects.create(subject='Sent', body='Original', sent_at=timezone.now())
        delivery = old.get_model('portal', 'Delivery').objects.create(digest=digest, subscriber=subscriber)
        draft = old.get_model('portal', 'Digest').objects.create(subject='Draft', body='Editable')
        executor = MigrationExecutor(connection)
        executor.migrate(latest)
        new = executor.loader.project_state(latest).apps
        migrated_event = new.get_model('events', 'Event').objects.get(pk=event.pk)
        assert migrated_event.slug == 'legacy'
        assert migrated_event.description_html == '<p>Описание</p>'
        assert not hasattr(migrated_event, 'register_url')
        tables = connection.introspection.table_names()
        assert not any(table in tables for table in ['meetups_talk', 'meetups_speaker', 'meetups_employer'])
        migrated = new.get_model('portal', 'Delivery').objects.get(pk=delivery.pk)
        assert migrated.state == 'sent' and migrated.email == 'legacy@example.org'
        assert migrated.sent_at == delivery.sent_at
        assert new.get_model('portal', 'Digest').objects.get(pk=digest.pk).state == 'sent'
        assert new.get_model('portal', 'Digest').objects.get(pk=draft.pk).state == 'draft'
    finally:
        MigrationExecutor(connection).migrate(latest)
