from datetime import date
from io import BytesIO

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from apps.banners.admin import BannerAdminForm
from apps.banners.models import Banner, Position


def uploaded_image():
    output = BytesIO()
    Image.new('RGB', (100, 20)).save(output, format='PNG')
    return SimpleUploadedFile('banner.png', output.getvalue(), content_type='image/png')


def banner_data(position, **changes):
    data = {
        'name': 'Весенняя конференция',
        'link_to': 'https://example.test/conference',
        'positions': [str(position.pk)],
        'width': '100%',
        'height': '300px',
        'date_from': date(2025, 4, 1).isoformat(),
        'date_to': '',
        'weekdays': ['2', '8'],
        'date_time_from': '9',
        'date_time_to': '18',
        'priority': '50',
        'active': 'on',
    }
    data.update(changes)
    return data


@pytest.mark.django_db
def test_banner_admin_uses_weekday_checkboxes_and_supported_slots_only(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    top = Position.objects.get(tag='top')
    legacy_position = Position.objects.create(name='Старое место', tag='legacy-slot')
    image = uploaded_image()

    form = BannerAdminForm(
        data=banner_data(top),
        files={'file_img': image},
    )

    assert legacy_position not in form.fields['positions'].queryset
    assert form.is_valid(), form.errors

    banner = form.save()
    assert banner.date_days == 10
    assert list(banner.positions.all()) == [top]
    assert banner.date_to is None


@pytest.mark.django_db
def test_banner_admin_validates_image_url_dimensions_and_schedule():
    top = Position.objects.get(tag='top')
    invalid = BannerAdminForm(
        data=banner_data(
            top,
            link_to='javascript:alert(1)',
            width='100px; color: red',
            date_to='2025-03-31',
            date_time_from='12',
            date_time_to='12',
        ),
        files={'file_img': SimpleUploadedFile('banner.png', b'image')},
    )

    assert not invalid.is_valid()
    assert {'link_to', 'width', 'date_to', 'date_time_to'} <= set(invalid.errors)

    missing_image = BannerAdminForm(data=banner_data(top))
    assert not missing_image.is_valid()
    assert 'file_img' in missing_image.errors

    fake_image = BannerAdminForm(
        data=banner_data(top),
        files={'file_img': SimpleUploadedFile('banner.png', b'not an image')},
    )
    assert not fake_image.is_valid()
    assert 'file_img' in fake_image.errors


@pytest.mark.django_db
def test_create_edit_and_disable_banner_through_admin(admin_client, client, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    top = Position.objects.get(tag='top')
    bottom = Position.objects.get(tag='bottom')
    data = banner_data(
        top, positions=[str(top.pk), str(bottom.pk)],
        date_from='2020-01-01', weekdays=['2', '4', '8', '16', '32', '64', '128'],
        date_time_from='0', date_time_to='24',
    )
    response = admin_client.get('/admin/banners/banner/add/')
    assert response.status_code == 200
    assert 'id_weekdays' in response.content.decode()
    response = admin_client.post('/admin/banners/banner/add/', {**data, 'file_img': uploaded_image()})
    assert response.status_code == 302
    banner = Banner.objects.get(name=data['name'])
    assert banner.positions.count() == 2
    assert client.get('/').content.decode().count('data-banner-position=') == 2

    edit_url = f'/admin/banners/banner/{banner.pk}/change/'
    response = admin_client.get(edit_url)
    assert response.status_code == 200
    assert banner.file_img.url in response.content.decode()
    # Editing should retain the existing image without requiring a new upload.
    data.pop('active')
    response = admin_client.post(edit_url, data)
    assert response.status_code == 302
    banner.refresh_from_db()
    assert not banner.active
    assert 'data-banner-position=' not in client.get('/').content.decode()
