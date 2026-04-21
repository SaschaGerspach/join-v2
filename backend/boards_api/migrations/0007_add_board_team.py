import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("boards_api", "0006_add_member_role"),
        ("teams_api", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="board",
            name="team",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="boards",
                to="teams_api.team",
            ),
        ),
    ]
