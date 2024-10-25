# Generated by Django 2.2.25 on 2022-01-12 06:35

from django.db import migrations
import enumerify.fields


class Migration(migrations.Migration):

    dependencies = [
        ('pharmacy', '0151_purchase_invoice_group'),
    ]

    operations = [
        migrations.AlterField(
            model_name='purchase',
            name='system_platform',
            field=enumerify.fields.SelectIntegerField(choices=[(0, '-'), (1, 'Un Identified'), (2, 'Web App'), (3, 'Android App'), (4, 'IOS App'), (5, 'E-commerce Web'), (6, 'Procurement Web')], db_index=True, default=2, help_text='Define system playform web/android-app/ios-app'),
        ),
    ]
