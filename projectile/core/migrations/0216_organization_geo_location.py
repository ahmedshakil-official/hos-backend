# Generated by Django 4.1.5 on 2023-05-08 07:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0215_personorganization_tagged_supplier'),
    ]

    operations = [
        migrations.AddField(
            model_name='organization',
            name='geo_location',
            field=models.JSONField(blank=True, default=dict, null=True),
        ),
    ]
