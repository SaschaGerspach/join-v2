from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("auth_api", "0002_add_is_verified"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="totp_secret",
            field=models.CharField(blank=True, default="", max_length=32),
        ),
        migrations.AddField(
            model_name="user",
            name="totp_enabled",
            field=models.BooleanField(default=False),
        ),
    ]
