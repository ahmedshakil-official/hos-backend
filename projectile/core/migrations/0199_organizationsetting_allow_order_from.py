# Generated by Django 2.2.20 on 2021-06-23 10:30

from django.db import migrations
import enumerify.fields


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0198_auto_20210531_1332'),
    ]

    operations = [
        migrations.AddField(
            model_name='organizationsetting',
            name='allow_order_from',
            field=enumerify.fields.SelectIntegerField(choices=[(0, '-'), (1, 'Only Stock'), (2, 'Stock and Next Day'), (3, 'Open')], db_index=True, default=3, help_text='Choices for product order from for ecommerce'),
        ),
    ]
