# Generated by Django 4.1.4 on 2023-01-03 15:42

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('expo_notification', '0003_pushtoken_app_version'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pushnotification',
            name='entry_by',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='%(app_label)s_%(class)s_entry_by', to=settings.AUTH_USER_MODEL, verbose_name='entry by'),
        ),
        migrations.AlterField(
            model_name='pushnotification',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='pushnotification',
            name='updated_by',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='%(app_label)s_%(class)s_updated_by', to=settings.AUTH_USER_MODEL, verbose_name='last updated by'),
        ),
        migrations.AlterField(
            model_name='pushtoken',
            name='entry_by',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='%(app_label)s_%(class)s_entry_by', to=settings.AUTH_USER_MODEL, verbose_name='entry by'),
        ),
        migrations.AlterField(
            model_name='pushtoken',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='pushtoken',
            name='updated_by',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='%(app_label)s_%(class)s_updated_by', to=settings.AUTH_USER_MODEL, verbose_name='last updated by'),
        ),
    ]
