# Generated by Django 5.0.4 on 2024-05-06 17:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0002_course_is_active'),
    ]

    operations = [
        migrations.CreateModel(
            name='Announcement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('custom_date', models.DateTimeField(blank=True, null=True)),
                ('content', models.TextField()),
            ],
        ),
    ]
