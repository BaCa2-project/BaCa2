from pathlib import Path

from django.db import migrations, models


class MigrationSettings:
    IN_COURSE: bool = False
    MODEL_NAME: str = 'packageinstance'
    FIELD_NAME: str = 'pdf_docs'
    APP_NAME: str = 'package'
    MEDIA_PATH_PREFIX: str = 'task_descriptions/'
    NULLABLE: bool = True


def reupload_submits(apps, schema_editor):
    from django.core.files import File

    from course.routing import OptionalInCourse
    from util.models_registry import ModelsRegistry
    sett = MigrationSettings()

    course_ = None
    if sett.IN_COURSE:
        course_name = schema_editor.connection.alias
        if course_name in ('default', 'baca2db'):
            return
        if course_name.endswith('_db'):
            course_name = course_name[:-3]
        course_model = apps.get_model('main', 'Course')
        try:
            course_ = ModelsRegistry.get_course(course_name)
        except course_model.DoesNotExist:
            return
    with OptionalInCourse(course_):
        file_model = apps.get_model(sett.APP_NAME, sett.MODEL_NAME)
        for file_field in file_model.objects.all():
            file_path = str(getattr(file_field, sett.FIELD_NAME))
            if not file_path and sett.NULLABLE:
                continue
            if file_path.startswith(sett.MEDIA_PATH_PREFIX):
                return
            with open(file_path, mode='rb') as f:
                setattr(file_model,
                        sett.FIELD_NAME,
                        File(f, name=Path(file_path).name)
                        )
                file_model.save()


class Migration(migrations.Migration):
    sett = MigrationSettings()

    dependencies = [
        ('package', '0002_alter_packageinstance_pdf_docs_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name=sett.MODEL_NAME,
            old_name=sett.FIELD_NAME,
            new_name=sett.FIELD_NAME + '__path'
        ),
        migrations.AddField(
            model_name=sett.MODEL_NAME,
            name=sett.FIELD_NAME,
            field=models.FileField(null=True, upload_to=sett.MEDIA_PATH_PREFIX)
        ),
        migrations.RunPython(reupload_submits),
        migrations.AlterField(
            model_name=sett.MODEL_NAME,
            name=sett.FIELD_NAME,
            field=models.FileField(blank=sett.NULLABLE,
                                   null=sett.NULLABLE,
                                   default=None if sett.NULLABLE else '/dev/null',
                                   upload_to=sett.MEDIA_PATH_PREFIX),
            preserve_default=False,
        ),
        migrations.RemoveField(
            model_name=sett.MODEL_NAME,
            name=sett.FIELD_NAME + '__path'
        ),
    ]
