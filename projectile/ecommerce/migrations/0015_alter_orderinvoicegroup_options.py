# Generated by Django 4.1.6 on 2023-05-18 11:32

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ecommerce', '0014_orderinvoicegroup_customer_comment_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='orderinvoicegroup',
            options={'ordering': ('-pk',), 'verbose_name': 'Order Invoice Group', 'verbose_name_plural': 'Order Invoice Groups'},
        ),
    ]
