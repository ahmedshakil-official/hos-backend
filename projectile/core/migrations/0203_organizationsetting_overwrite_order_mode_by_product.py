# Generated by Django 2.2.20 on 2021-07-26 09:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0202_auto_20210715_1433'),
    ]

    operations = [
        migrations.AddField(
            model_name='organizationsetting',
            name='overwrite_order_mode_by_product',
            field=models.BooleanField(default=False, help_text='Decide overwrite order mode from settings or not'),
        ),
    ]
