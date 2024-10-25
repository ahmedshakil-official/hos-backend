# Generated by Django 2.2.13 on 2020-11-30 11:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pharmacy', '0139_auto_20201117_1315'),
    ]

    operations = [
        migrations.AddField(
            model_name='purchase',
            name='additional_cost',
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name='purchase',
            name='additional_cost_rate',
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name='purchase',
            name='additional_discount',
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name='purchase',
            name='additional_discount_rate',
            field=models.FloatField(default=0.0),
        ),
    ]
