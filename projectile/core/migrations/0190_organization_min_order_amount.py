# Generated by Django 2.2.13 on 2020-10-20 05:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0189_organizationsetting_enable_stock_fixing_celery_task'),
    ]

    operations = [
        migrations.AddField(
            model_name='organization',
            name='min_order_amount',
            field=models.FloatField(default=0.0),
        ),
    ]