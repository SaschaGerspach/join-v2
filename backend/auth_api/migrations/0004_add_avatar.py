from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("auth_api", "0003_add_totp_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="avatar",
            field=models.ImageField(blank=True, default="", upload_to="avatars/"),
        ),
    ]
