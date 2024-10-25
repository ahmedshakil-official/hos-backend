# Generated by Django 2.2.13 on 2020-07-08 09:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0183_auto_20200630_2032'),
    ]

    operations = [
        migrations.AddField(
            model_name='organizationsetting',
            name='allow_procurement_product_add_edit',
            field=models.BooleanField(default=False, help_text='Settings for enable/disable product add/edit permission for procurement'),
        ),
    ]
