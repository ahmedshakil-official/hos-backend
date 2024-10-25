# Generated by Django 4.2.2 on 2023-10-12 10:41

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0219_otp_passwordreset'),
    ]

    operations = [
        migrations.AddField(
            model_name='person',
            name='delivery_hub',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='person_delivery_hub', to='core.deliveryhub'),
        ),
        migrations.AddField(
            model_name='person',
            name='permissions',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='personorganization',
            name='delivery_hub',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='person_organization_delivery_hub', to='core.deliveryhub'),
        ),
        migrations.AddField(
            model_name='personorganization',
            name='permissions',
            field=models.TextField(blank=True),
        ),
    ]
