# Generated by Django 4.1.5 on 2023-04-27 10:15

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ecommerce', '0013_wishlistitem_sell_quantity_per_week_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderinvoicegroup',
            name='customer_comment',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='orderinvoicegroup',
            name='customer_rating',
            field=models.PositiveIntegerField(default=0, validators=[django.core.validators.MaxValueValidator(5), django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='orderinvoicegroup',
            name='delivered_at',
            field=models.DateTimeField(blank=True, help_text='When Porter delivered the order', null=True),
        ),
    ]
