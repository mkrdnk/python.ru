from datetime import date

import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor


@pytest.mark.django_db(transaction=True)
def test_banner_position_migration_preserves_legacy_association_and_seeds_slots():
    executor = MigrationExecutor(connection)
    executor.migrate([('banners', '0001_initial')])
    old_apps = executor.loader.project_state([('banners', '0001_initial')]).apps
    LegacyBanner = old_apps.get_model('banners', 'Banner')
    LegacyPosition = old_apps.get_model('banners', 'Position')

    legacy_position = LegacyPosition.objects.create(name='Старое место', tag='legacy-slot')
    legacy_banner = LegacyBanner.objects.create(
        name='Старый баннер',
        file_img='data-img/legacy.png',
        link_to='https://example.test/legacy',
        date_from=date(2025, 1, 1),
        date_to=date(2025, 1, 31),
        priority=1,
        active=True,
        position=legacy_position,
    )

    executor = MigrationExecutor(connection)
    executor.migrate([('banners', '0002_banner_positions')])
    new_apps = executor.loader.project_state([('banners', '0002_banner_positions')]).apps
    Banner = new_apps.get_model('banners', 'Banner')
    Position = new_apps.get_model('banners', 'Position')

    migrated_banner = Banner.objects.get(pk=legacy_banner.pk)
    assert list(migrated_banner.positions.values_list('pk', flat=True)) == [legacy_position.pk]
    assert Position.objects.filter(pk=legacy_position.pk, tag='legacy-slot').exists()
    assert set(Position.objects.filter(
        tag__in=('top', 'sidebar', 'article_end', 'bottom'),
    ).values_list('tag', flat=True)) == {'top', 'sidebar', 'article_end', 'bottom'}
