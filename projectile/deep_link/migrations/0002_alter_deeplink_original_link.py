# Generated by Django 4.2.3 on 2023-08-22 09:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('deep_link', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='deeplink',
            name='original_link',
            field=models.URLField(),
        ),
    ]