# Generated by Django 2.2.8 on 2019-12-24 10:05

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import enumerify.fields
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0170_auto_20191213_0714'),
    ]

    operations = [
        migrations.CreateModel(
            name='Promotion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('alias', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
                ('status', enumerify.fields.SelectIntegerField(choices=[(0, 'Active'), (1, 'Inactive'), (2, 'Draft'), (3, 'Released'), (4, 'Approved Draft'), (5, 'Absent'), (6, 'Purchase Order'), (7, 'Suspend'), (8, 'On Hold'), (9, 'Hardwired'), (10, 'Loss'), (11, 'Freeze'), (12, 'For Adjustment')], db_index=True, default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('organization_wise_serial', models.PositiveIntegerField(default=0, editable=False, help_text='OrganizationWise Serial Number')),
                ('user_ip', models.GenericIPAddressField(blank=True, editable=False, null=True)),
                ('message', models.TextField()),
                ('entry_by', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='promotion_promotion_entry_by', to=settings.AUTH_USER_MODEL, verbose_name='entry by')),
                ('updated_by', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='promotion_promotion_updated_by', to=settings.AUTH_USER_MODEL, verbose_name='last updated by')),
            ],
            options={
                'verbose_name_plural': 'Promotions',
            },
        ),
        migrations.CreateModel(
            name='PublishedPromotion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('alias', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
                ('status', enumerify.fields.SelectIntegerField(choices=[(0, 'Active'), (1, 'Inactive'), (2, 'Draft'), (3, 'Released'), (4, 'Approved Draft'), (5, 'Absent'), (6, 'Purchase Order'), (7, 'Suspend'), (8, 'On Hold'), (9, 'Hardwired'), (10, 'Loss'), (11, 'Freeze'), (12, 'For Adjustment')], db_index=True, default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('organization_wise_serial', models.PositiveIntegerField(default=0, editable=False, help_text='OrganizationWise Serial Number')),
                ('user_ip', models.GenericIPAddressField(blank=True, editable=False, null=True)),
                ('entry_by', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='promotion_publishedpromotion_entry_by', to=settings.AUTH_USER_MODEL, verbose_name='entry by')),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='core.Organization', verbose_name='organization name')),
                ('promotion', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='published_promotions', to='promotion.Promotion')),
                ('updated_by', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='promotion_publishedpromotion_updated_by', to=settings.AUTH_USER_MODEL, verbose_name='last updated by')),
            ],
            options={
                'verbose_name_plural': 'Published Promotions',
                'index_together': {('organization', 'promotion')},
            },
        ),
    ]
