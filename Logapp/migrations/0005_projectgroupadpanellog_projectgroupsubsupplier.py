# Generated by Django 5.0.6 on 2025-03-25 17:51

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Logapp', '0004_customerlog_customer_and_more'),
        ('Project', '0073_alter_project_project_revenue_month_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='projectgroupadpanellog',
            name='projectgroupsubsupplier',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='Project.projectgroupsubsupplier'),
        ),
    ]
