from celery import shared_task
from django.utils import timezone


@shared_task
def check_deadline_rules():
    from tasks_api.models import Task
    from .engine import evaluate_rules
    from .models import AutomationRule, TriggerType

    rules = list(
        AutomationRule.objects.filter(
            trigger_type=TriggerType.DEADLINE_APPROACHING,
            is_active=True,
        ).prefetch_related("conditions", "actions")
    )
    if not rules:
        return

    max_hours = max(r.trigger_config.get("hours", 24) for r in rules)
    threshold = timezone.now() + timezone.timedelta(hours=max_hours)
    tasks = Task.objects.filter(
        due_date__isnull=False,
        due_date__lte=threshold.date(),
        due_date__gte=timezone.now().date(),
        archived_at__isnull=True,
    )

    for task in tasks:
        evaluate_rules(task, TriggerType.DEADLINE_APPROACHING)
