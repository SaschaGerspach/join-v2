from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tasks_api", "0018_add_archived_at_index"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="comment",
            index=models.Index(fields=["task", "created_at"], name="tasks_api_co_task_id_created_idx"),
        ),
    ]
