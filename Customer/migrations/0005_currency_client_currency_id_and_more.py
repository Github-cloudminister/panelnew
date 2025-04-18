# Generated by Django 4.0.6 on 2022-12-20 12:19

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('Customer', '0004_alter_clientcontact_id_alter_currency_id_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='currency',
            name='client_currency_id',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='currency',
            name='client_currency_name',
            field=models.CharField(max_length=80, null=True),
        ),
        migrations.AddField(
            model_name='currency',
            name='customer_name',
            field=models.CharField(max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='customerorganization',
            name='customer_url_code',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='currency',
            name='currency_iso',
            field=models.CharField(max_length=3, null=True),
        ),
        migrations.AlterField(
            model_name='currency',
            name='currency_name',
            field=models.CharField(max_length=60, null=True, unique=True),
        ),
        migrations.CreateModel(
            name='CustomerOrgAuthKeyDetails',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('authkey', models.CharField(blank=True, max_length=200, null=True)),
                ('staging_authkey', models.CharField(blank=True, max_length=200, null=True)),
                ('api_key', models.CharField(blank=True, max_length=200, null=True)),
                ('staging_api_key', models.CharField(blank=True, max_length=200, null=True)),
                ('secret_key', models.CharField(blank=True, max_length=200, null=True)),
                ('staging_secret_key', models.CharField(blank=True, max_length=200, null=True)),
                ('staging_base_url', models.URLField(blank=True, null=True)),
                ('production_base_url', models.URLField(blank=True, null=True)),
                ('client_id', models.CharField(blank=True, max_length=100, null=True)),
                ('supplier_id', models.CharField(blank=True, max_length=30, null=True)),
                ('customerOrg', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='authkey_detail', to='Customer.customerorganization')),
            ],
        ),
    ]
