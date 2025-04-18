# Generated by Django 4.0.6 on 2024-04-23 13:46

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('employee', '0004_alter_country_id_alter_employeeprofile_id'),
        ('Questions', '0010_parentanswer_lucid_answer_id_and_more'),
        ('Project', '0055_alter_projectgroupsubsupplier_project_group_supplier'),
        ('affiliaterouter', '0012_visitors_subsource'),
    ]

    operations = [
        migrations.CreateModel(
            name='RouterException',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('detailed_reason', models.CharField(blank=True, max_length=100000, null=True)),
            ],
        ),
        migrations.RemoveConstraint(
            model_name='affiliaterouterquestionsdata',
            name='unique_visitor_parent_question',
        ),
        migrations.AlterField(
            model_name='affiliaterouterquestionsdata',
            name='country',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='employee.country'),
        ),
        migrations.AlterField(
            model_name='affiliaterouterquestionsdata',
            name='language',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Project.language'),
        ),
        migrations.AlterField(
            model_name='affiliaterouterquestionsdata',
            name='parent_question',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Questions.translatedquestion'),
        ),
        migrations.AlterField(
            model_name='affiliaterouterquestionsdata',
            name='visitor',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='affiliaterouter.visitors'),
        ),
        migrations.AddField(
            model_name='routerexception',
            name='visitor',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='affiliaterouter.visitors'),
        ),
    ]
