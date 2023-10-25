# Generated by Django 4.2.6 on 2023-10-25 17:48

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0010_alter_rolepreset_permissions'),
    ]

    operations = [
        migrations.AlterField(
            model_name='course',
            name='admin_role',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='main.role', verbose_name='admin role'),
        ),
        migrations.AlterField(
            model_name='course',
            name='default_role',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='main.role', verbose_name='default role'),
        ),
    ]
