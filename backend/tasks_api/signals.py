import django.dispatch

task_created = django.dispatch.Signal()
task_moved = django.dispatch.Signal()
task_priority_changed = django.dispatch.Signal()
task_label_added = django.dispatch.Signal()
all_subtasks_completed = django.dispatch.Signal()
