from django.contrib import admin

from .models import AutomationRule, RuleAction, RuleCondition, AutomationLog


class RuleConditionInline(admin.TabularInline):
    model = RuleCondition
    extra = 0


class RuleActionInline(admin.TabularInline):
    model = RuleAction
    extra = 0


@admin.register(AutomationRule)
class AutomationRuleAdmin(admin.ModelAdmin):
    list_display = ["name", "board", "trigger_type", "is_active", "is_default", "created_at"]
    list_filter = ["is_active", "trigger_type"]
    inlines = [RuleConditionInline, RuleActionInline]


@admin.register(AutomationLog)
class AutomationLogAdmin(admin.ModelAdmin):
    list_display = ["rule", "task", "trigger_type", "executed_at"]
    list_filter = ["trigger_type"]
    readonly_fields = ["rule", "task", "board", "trigger_type", "actions_executed", "executed_at"]
