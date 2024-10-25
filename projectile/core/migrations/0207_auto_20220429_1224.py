# Generated by Django 2.2.25 on 2022-04-29 06:24

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0206_organization_referrer'),
    ]

    operations = [
        migrations.AddField(
            model_name='organization',
            name='primary_responsible_person',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='primary_responsible_person_organizations', to='core.PersonOrganization', verbose_name='Person Organization who are primary responsible person of this organization'),
        ),
        migrations.AddField(
            model_name='organization',
            name='secondary_responsible_person',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='secondary_responsible_person_organizations', to='core.PersonOrganization', verbose_name='Person Organization who are secondary responsible person of this organization'),
        ),
    ]