# Generated by Django 2.2.9 on 2020-02-07 10:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pharmacy', '0126_auto_20200116_1655'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='alias_name',
            field=models.CharField(blank=True, db_index=True, help_text='pseudonym/Alias of product', max_length=255, null=True),
        ),
    ]
