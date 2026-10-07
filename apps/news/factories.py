# coding: utf-8
from django.utils import timezone
import factory

from apps.news.models import Article


class ArticleFactory(factory.django.DjangoModelFactory):
    name = factory.Sequence(lambda n: u"article%s" % n)
    url = factory.Sequence(lambda n: u"http://hackernews.com/%s" % n)
    is_active = True
    published_at = factory.LazyAttribute(lambda o: timezone.now())

    class Meta:
        model = Article
