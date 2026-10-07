# coding: utf-8
import pytest
from django.urls import reverse

from apps.content.factories import LinkFactory
from apps.news.factories import ArticleFactory


@pytest.mark.django_db
def test_index(client):
    ArticleFactory(is_featured=True)
    ArticleFactory(is_active=False)

    LinkFactory()
    LinkFactory()

    response = client.get(reverse('index'))
    assert response.status_code == 200
