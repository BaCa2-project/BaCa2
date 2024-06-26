# Generated by Django 5.0.4 on 2024-04-24 18:36

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('package', '0004_change_package_attachments_storage'),
    ]

    operations = [
        migrations.AlterField(
            model_name='packageinstance',
            name='pdf_docs',
            field=models.FileField(blank=True, default=None, null=True,
                                   upload_to='task_descriptions/'),
        ),
        migrations.AlterField(
            model_name='packageinstanceattachment',
            name='path',
            field=models.FileField(blank=True, default=None, null=True, upload_to='attachments/'),
        ),
    ]
