from .models import ActivityEntry


def log_activity(board, user, action, entity_type, entity_title, details="", task=None):
    ActivityEntry.objects.create(
        board=board,
        user=user,
        action=action,
        entity_type=entity_type,
        entity_title=entity_title,
        details=details,
        task=task,
    )
