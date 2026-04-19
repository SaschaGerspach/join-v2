from django.db import migrations, models


def migrate_fk_to_m2m(apps, schema_editor):
    Task = apps.get_model('tasks_api', 'Task')
    for task in Task.objects.filter(assigned_to__isnull=False):
        task.assignees.add(task.assigned_to_id)


class Migration(migrations.Migration):

    dependencies = [
        ('contacts_api', '0002_alter_contact_unique_together'),
        ('tasks_api', '0010_task_archived_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='assignees',
            field=models.ManyToManyField(blank=True, related_name='assigned_tasks', to='contacts_api.contact'),
        ),
        migrations.RunPython(migrate_fk_to_m2m, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='task',
            name='assigned_to',
        ),
    ]
