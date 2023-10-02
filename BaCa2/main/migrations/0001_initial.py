# Generated by Django 4.2.5 on 2023-10-02 16:39

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='Course',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='course name')),
                ('short_name', models.CharField(max_length=20, unique=True, verbose_name='course short name')),
                ('USOS_course_code', models.CharField(blank=True, max_length=20, null=True, verbose_name='Subject code')),
                ('USOS_term_code', models.CharField(blank=True, max_length=20, null=True, verbose_name='Term code')),
                ('admin_role', models.ForeignKey(limit_choices_to={'groupcourse__course': None}, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='auth.group', verbose_name='admin role')),
                ('default_role', models.ForeignKey(limit_choices_to={'groupcourse__course': None}, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='auth.group', verbose_name='default role')),
            ],
        ),
        migrations.CreateModel(
            name='Settings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('theme', models.CharField(default='dark', max_length=255, verbose_name='UI theme')),
            ],
        ),
        migrations.CreateModel(
            name='GroupCourse',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.course')),
                ('group', models.ForeignKey(limit_choices_to={'groupcourse': None}, on_delete=django.db.models.deletion.CASCADE, to='auth.group')),
            ],
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('email', models.EmailField(max_length=255, unique=True, verbose_name='email address')),
                ('username', models.CharField(max_length=255, unique=True, verbose_name='username')),
                ('is_staff', models.BooleanField(default=False)),
                ('is_superuser', models.BooleanField(default=False)),
                ('first_name', models.CharField(blank=True, max_length=255, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=255, verbose_name='last name')),
                ('date_joined', models.DateField(auto_now_add=True)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
                ('user_settings', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='main.settings')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
