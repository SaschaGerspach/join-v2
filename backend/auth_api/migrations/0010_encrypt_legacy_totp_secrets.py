import re

from django.db import migrations

from auth_api.encryption import encrypt_totp_secret

# Secrets stored before encryption was introduced are raw base32; Fernet tokens never match this.
PLAINTEXT_SECRET = re.compile(r"[A-Z2-7]+=*")


def encrypt_plaintext_secrets(apps, schema_editor):
    User = apps.get_model("auth_api", "User")
    for user in User.objects.exclude(totp_secret="").only("pk", "totp_secret"):
        if PLAINTEXT_SECRET.fullmatch(user.totp_secret):
            user.totp_secret = encrypt_totp_secret(user.totp_secret)
            user.save(update_fields=["totp_secret"])


class Migration(migrations.Migration):

    dependencies = [
        ('auth_api', '0009_user_totp_last_counter'),
    ]

    operations = [
        migrations.RunPython(encrypt_plaintext_secrets, migrations.RunPython.noop),
    ]
