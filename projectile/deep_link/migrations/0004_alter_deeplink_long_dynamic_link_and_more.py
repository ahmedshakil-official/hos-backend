# Generated by Django 4.2.4 on 2023-11-03 05:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('deep_link', '0003_alter_deeplink_long_dynamic_link_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='deeplink',
            name='long_dynamic_link',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='deeplink',
            name='original_link',
            field=models.TextField(),
        ),
    ]
