# Generated by Django 5.0.6 on 2024-06-10 19:54

import django.db.models.deletion
from django.db import migrations, models

import course.models


class Migration(migrations.Migration):

    dependencies = [
        ('course', '0002_change_submit_source_code'),
    ]

    operations = [
        migrations.CreateModel(
            name='Ranking',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('usr', models.BigIntegerField(validators=[course.models.SubmitManager.user_exists_validator])),
                ('status', models.CharField(choices=[('PND', 'Pending'), ('OK', 'Accepted'), ('ANS', 'Wrong answer'), ('TLE', 'Time limit exceeded'), ('RTE', 'Runtime error'), ('MEM', 'Memory exceeded'), ('CME', 'Compilation error'), ('RUL', 'Rule violation'), ('EXT', 'Unknown extension'), ('ITL', 'Internal timeout'), ('INT', 'Internal error')], default='PND', max_length=3)),
                ('score', models.FloatField(default=None, null=True)),
                ('sum_time', models.FloatField(default=None, null=True)),
                ('sum_memory', models.IntegerField(default=None, null=True)),
                ('submits_amount', models.IntegerField(default=None, null=True)),
                ('task', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='course.task')),
            ],
        ),
    ]