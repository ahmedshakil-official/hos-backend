# Generated by Django 2.2.20 on 2021-07-13 05:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pharmacy', '0146_auto_20210706_1501'),
    ]

    operations = [
        migrations.AddField(
            model_name='purchase',
            name='tentative_delivery_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]
