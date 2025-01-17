# Generated by Django 4.2.4 on 2023-10-06 04:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('deep_link', '0002_alter_deeplink_original_link'),
    ]

    operations = [
        migrations.AlterField(
            model_name='deeplink',
            name='long_dynamic_link',
            field=models.URLField(blank=True, max_length=2048, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name='deeplink',
            name='original_link',
            field=models.URLField(max_length=2048),
        ),
    ]
