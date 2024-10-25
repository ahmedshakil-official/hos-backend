# Generated by Django 2.2.9 on 2019-12-31 10:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('promotion', '0004_publishedpromotionorder_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='publishedpromotionorder',
            name='contact_no',
            field=models.CharField(blank=True, default=None, help_text='Customer contact number', max_length=24, null=True),
        ),
    ]