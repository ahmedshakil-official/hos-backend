# Generated by Django 2.2.13 on 2020-10-21 11:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('expo_notification', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='pushnotification',
            name='response',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='pushnotification',
            name='title',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Name'),
        ),
    ]