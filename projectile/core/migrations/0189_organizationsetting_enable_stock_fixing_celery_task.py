# Generated by Django 2.2.13 on 2020-09-24 10:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0188_personorganization_dropout_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='organizationsetting',
            name='enable_stock_fixing_celery_task',
            field=models.BooleanField(default=False, help_text='Settings for enable/disable stock fixing celery task'),
        ),
    ]
