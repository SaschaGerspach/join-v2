import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('boards_api', '0003_add_board_color'),
        ('notifications_api', '0001_initial'),
        ('tasks_api', '0011_fk_to_m2m_assignees'),
    ]

    operations = [
        migrations.RenameField(
            model_name='notification',
            old_name='board_id',
            new_name='board',
        ),
        migrations.RenameField(
            model_name='notification',
            old_name='task_id',
            new_name='task',
        ),
        migrations.AlterField(
            model_name='notification',
            name='board',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to='boards_api.board',
            ),
        ),
        migrations.AlterField(
            model_name='notification',
            name='task',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to='tasks_api.task',
            ),
        ),
        migrations.AlterField(
            model_name='notification',
            name='type',
            field=models.CharField(
                choices=[('assignment', 'Assignment'), ('comment', 'Comment'), ('mention', 'Mention')],
                max_length=20,
            ),
        ),
    ]
