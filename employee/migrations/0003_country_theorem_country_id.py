# Generated by Django 3.1.1 on 2022-01-03 11:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('employee', '0002_auto_20211026_2246'),
    ]

    operations = [
        migrations.AddField(
            model_name='country',
            name='theorem_country_id',
            field=models.CharField(blank=True, default=None, max_length=250, null=True),
        ),
    ]
