# Generated by Django 2.2.9 on 2019-12-31 09:56

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('promotion', '0003_publishedpromotionorder'),
    ]

    operations = [
        migrations.AddField(
            model_name='publishedpromotionorder',
            name='date',
            field=models.DateTimeField(default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]