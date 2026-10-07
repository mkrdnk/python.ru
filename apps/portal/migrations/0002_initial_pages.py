from django.db import migrations


def initial_pages(apps, schema_editor):
    Page = apps.get_model('portal', 'Page')
    Community = apps.get_model('portal', 'Community')
    Page.objects.get_or_create(slug='about', defaults={
        'title': 'О Python.ru', 'is_active': True,
        'body': '<p>Python.ru — независимый портал русскоязычного Python-сообщества. '
                'Здесь собраны материалы о разработке, события, проекты и локальные сообщества.</p>'
                '<p>Хотите поделиться опытом? <a href="/contribute/">Предложите материал редакции.</a></p>'})
    Page.objects.get_or_create(slug='editorial', defaults={
        'title': 'Редакция', 'is_active': True,
        'body': '<p>Python.ru создаётся сообществом. Мы принимаем статьи, заметки, '
                'анонсы событий и предложения Open Source проектов.</p>'
                '<p><a href="/contribute/">Отправить предложение</a></p>'})
    Community.objects.get_or_create(url='https://moscowpython.ru/', defaults={
        'name': 'Moscow Python', 'city': 'Москва', 'is_active': True,
        'description': 'Сообщество Python-разработчиков.'})


class Migration(migrations.Migration):
    dependencies = [('portal', '0001_initial')]
    operations = [migrations.RunPython(initial_pages, migrations.RunPython.noop)]
