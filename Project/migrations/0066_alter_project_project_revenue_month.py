# Generated by Django 5.0.8 on 2024-08-20 18:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Project', '0065_projectgroupprioritystats'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='project_revenue_month',
            field=models.CharField(choices=[('1', 'January'), ('2', 'February'), ('3', 'March'), ('4', 'April'), ('5', 'May'), ('6', 'June'), ('7', 'July'), ('8', 'August'), ('9', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December')], default=8, max_length=2),
        ),
    ]
