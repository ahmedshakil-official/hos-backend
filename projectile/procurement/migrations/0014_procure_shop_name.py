# Generated by Django 2.2.25 on 2022-07-20 09:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('procurement', '0013_procure_medium'),
    ]

    operations = [
        migrations.AddField(
            model_name='procure',
            name='shop_name',
            field=models.CharField(blank=True, help_text='The name will be user for print header', max_length=128, null=True, verbose_name='shop name'),
        ),
    ]
