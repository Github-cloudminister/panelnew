# Generated by Django 3.1.1 on 2022-06-02 16:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Supplier', '0011_auto_20220416_0155'),
    ]

    operations = [
        migrations.AddField(
            model_name='supplierorgauthkeydetails',
            name='staging_api_key',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='supplierorgauthkeydetails',
            name='staging_authkey',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='supplierorgauthkeydetails',
            name='staging_secret_key',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]
