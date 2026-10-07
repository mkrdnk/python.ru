from io import BytesIO

from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from apps.news.factories import ArticleFactory


def test_article_admin_uses_editor_and_escapes_titles(admin_client):
    article = ArticleFactory(name='<script>alert(1)</script>')
    response = admin_client.get(reverse('admin:news_article_changelist'))
    assert response.status_code == 200
    assert b'&lt;script&gt;alert(1)&lt;/script&gt;' in response.content
    response = admin_client.get(reverse('admin:news_article_change', args=[article.pk]))
    assert response.status_code == 200
    assert b'django_ckeditor_5/dist/bundle.js' in response.content
    assert b'ckeditor/ckeditor.js' not in response.content


def test_editor_upload_requires_staff(client, admin_client, settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path)
    url = reverse('ck_editor_5_upload_file')
    assert client.post(url).status_code == 403
    image = BytesIO()
    Image.new('RGB', (2, 2)).save(image, format='PNG')
    response = admin_client.post(url, {
        'upload': SimpleUploadedFile('editor-test.png', image.getvalue(), content_type='image/png'),
    })
    assert response.status_code == 200
    assert response.json()['url'].startswith('/media/')
    assert len(list(tmp_path.glob('*.png'))) == 1
