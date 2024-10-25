# Generated by Django 2.2.13 on 2020-07-17 09:18

from django.db import migrations
import enumerify.fields


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0075_auto_20200225_1539'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transaction',
            name='transaction_for',
            field=enumerify.fields.SelectIntegerField(choices=[(0, '-'), (1, 'Sale'), (2, 'Admission'), (3, 'Appointment'), (4, 'Service Consumed'), (5, 'Others'), (6, 'Purchase'), (7, 'Person Payable')], db_index=True, default=5),
        ),
    ]
