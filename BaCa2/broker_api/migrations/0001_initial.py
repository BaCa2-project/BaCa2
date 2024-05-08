# Generated by Django 5.0.4 on 2024-04-22 18:40

import django.utils.timezone
from django.db import migrations, models

import broker_api.models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='BrokerSubmit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False,
                                           verbose_name='ID')),
                ('submit_id', models.BigIntegerField()),
                ('status', models.IntegerField(default=0,
                                               verbose_name=broker_api.models.BrokerSubmit.StatusEnum)),
                ('update_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('retry_amount', models.IntegerField(default=0)),
            ],
        ),
    ]