# Generated by Django 4.2.6 on 2023-10-26 10:39

from django.db import migrations, models
import pathlib


class Migration(migrations.Migration):

    dependencies = [
        ('course', '0004_alter_submit_source_code'),
    ]

    operations = [
        migrations.AlterField(
            model_name='submit',
            name='source_code',
            field=models.FilePathField(path=pathlib.PureWindowsPath('C:/Users/user/Desktop/stuff/projects/baca2_project/baca2/BaCa2/submits')),
        ),
    ]