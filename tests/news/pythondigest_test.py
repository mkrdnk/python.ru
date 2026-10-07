# coding: utf-8
import datetime
import vcr
from django.core.management import call_command
from datetime import timezone

utc = timezone.utc

from apps.news.models import Article

my_vcr = vcr.VCR(
    cassette_library_dir='tests/cassettes',
    record_mode='once',
    path_transformer=vcr.VCR.ensure_suffix('.yaml'),
    decode_compressed_response=True
)


@my_vcr.use_cassette
def test_pythondigest(db):
    call_command('pythondigest')

    assert Article.objects.count() == 10

    article = Article.objects.order_by('-published_at', 'id').last()
    assert article.url == 'http://github.com/PokemonGoF/PokemonGo-Bot'
    assert article.name == 'PokemonGo-Bot - бот для поиска покемонов'
    assert article.description == ''
    assert article.published_at == datetime.datetime(2016, 7, 24, 11, 1, 36, tzinfo=utc)
    assert not article.is_active
    assert not article.is_featured
    assert article.source == 'pythondigest'

    article = Article.objects.order_by('-published_at', 'id').first()
    assert article.description == '<p>Плейлист с видео с конференции SciPy 2016</p>'


@my_vcr.use_cassette
def test_pythondigest_daterange(db):
    call_command('pythondigest', days=2, till_date='2016-10-29')

    assert Article.objects.count() == 2
