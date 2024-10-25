# Generated by Django 4.2.2 on 2023-08-07 06:14

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pharmacy', '0164_stock_last_publish_stock_last_unpublish'),
    ]

    operations = [
        migrations.AddField(
            model_name='purchase',
            name='order_rating',
            field=models.IntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)]),
        ),
        migrations.AddField(
            model_name='purchase',
            name='order_rating_comment',
            field=models.TextField(blank=True, null=True),
        ),
    ]