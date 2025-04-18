# Generated by Django 3.1.1 on 2021-11-29 20:03

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('SupplierInvoice', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='supplierinvoice',
            name='completes',
            field=models.IntegerField(default=1, validators=[django.core.validators.MinValueValidator(1)]),
        ),
        migrations.AddField(
            model_name='supplierinvoice',
            name='cpi',
            field=models.FloatField(default=0),
        ),
        migrations.AlterField(
            model_name='supplierinvoice',
            name='invoice_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='supplierinvoice',
            name='invoice_number',
            field=models.CharField(blank=True, default='', max_length=50, null=True),
        ),
    ]
