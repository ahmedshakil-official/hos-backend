# Generated by Django 2.2.10 on 2020-06-08 06:38

from django.db import migrations
import enumerify.fields


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0179_auto_20200604_1236'),
    ]

    operations = [
        migrations.AlterField(
            model_name='organization',
            name='type',
            field=enumerify.fields.SelectIntegerField(choices=[(0, 'Mother'), (1, 'Branch'), (2, 'Unite'), (3, 'Private Practitioners'), (4, 'Pharmacy'), (5, 'Diagnostic'), (6, 'Distributor'), (7, 'Distributor Buyer')], db_index=True, default=0),
        ),
    ]