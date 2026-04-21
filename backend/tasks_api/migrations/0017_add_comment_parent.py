import django.db.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tasks_api", "0016_add_time_entry"),
    ]

    operations = [
        migrations.AddField(
            model_name="comment",
            name="parent",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="replies",
                to="tasks_api.comment",
            ),
        ),
    ]
