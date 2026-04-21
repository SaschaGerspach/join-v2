import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AuditLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("event_type", models.CharField(
                    max_length=40,
                    choices=[
                        ("login_success", "Login Success"),
                        ("login_failed", "Login Failed"),
                        ("password_reset", "Password Reset"),
                        ("totp_enabled", "Totp Enabled"),
                        ("totp_disabled", "Totp Disabled"),
                        ("board_member_added", "Board Member Added"),
                        ("board_member_removed", "Board Member Removed"),
                        ("board_member_role_changed", "Board Member Role Changed"),
                        ("team_member_added", "Team Member Added"),
                        ("team_member_removed", "Team Member Removed"),
                        ("team_member_role_changed", "Team Member Role Changed"),
                        ("account_deleted", "Account Deleted"),
                        ("admin_action", "Admin Action"),
                    ],
                )),
                ("detail", models.TextField(blank=True, default="")),
                ("ip_address", models.GenericIPAddressField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("user", models.ForeignKey(
                    blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                    related_name="audit_logs", to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                "ordering": ["-created_at"],
                "indexes": [models.Index(fields=["event_type", "created_at"], name="audit_api_a_event_t_idx")],
            },
        ),
    ]
