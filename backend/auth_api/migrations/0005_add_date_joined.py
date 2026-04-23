import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("auth_api", "0004_add_avatar"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="date_joined",
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]
