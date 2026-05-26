from django.apps import AppConfig


class TasksApiConfig(AppConfig):
    name = 'tasks_api'

    def ready(self):
        from django.db.models.signals import post_delete
        from .models import Attachment

        post_delete.connect(_delete_attachment_file, sender=Attachment)


def _delete_attachment_file(sender, instance, **kwargs):
    if instance.file:
        instance.file.delete(save=False)
