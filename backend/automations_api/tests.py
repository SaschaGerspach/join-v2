from unittest.mock import patch

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from boards_api.models import Board
from columns_api.models import Column
from contacts_api.models import Contact
from tasks_api.models import Label, Task

from .conditions import check_condition
from .engine import _trigger_matches, evaluate_rules, models_q_board_or_global
from .models import (
    ActionType,
    AutomationLog,
    AutomationRule,
    ConditionType,
    RuleAction,
    RuleCondition,
    TriggerType,
)

User = get_user_model()


class AutomationTestMixin:
    def setUp(self):
        self.user = User.objects.create_user(email="owner@example.com", password="pass")
        self.other = User.objects.create_user(email="other@example.com", password="pass")
        self.board = Board.objects.create(title="Test Board", created_by=self.user)
        self.col1 = Column.objects.create(board=self.board, title="Todo", order=0)
        self.col2 = Column.objects.create(board=self.board, title="Done", order=1)
        self.task = Task.objects.create(board=self.board, column=self.col1, title="Test Task", priority="medium")


# ---------------------------------------------------------------------------
# View Tests — CRUD
# ---------------------------------------------------------------------------

class RuleListTests(AutomationTestMixin, APITestCase):
    def setUp(self):
        super().setUp()
        self.client.force_authenticate(user=self.user)
        self.url = f"/boards/{self.board.pk}/automations/"

    def _create_payload(self, **overrides):
        data = {
            "name": "Auto Rule",
            "trigger_type": TriggerType.TASK_CREATED,
            "actions": [{"action_type": ActionType.SET_PRIORITY, "config": {"priority": "high"}}],
        }
        data.update(overrides)
        return data

    def test_list_empty(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data, [])

    def test_list_returns_rules(self):
        AutomationRule.objects.create(
            board=self.board, created_by=self.user,
            name="R1", trigger_type=TriggerType.TASK_CREATED,
        )
        resp = self.client.get(self.url)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]["name"], "R1")

    def test_create_rule(self):
        resp = self.client.post(self.url, self._create_payload(), format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["name"], "Auto Rule")
        self.assertEqual(resp.data["trigger_type"], TriggerType.TASK_CREATED)
        self.assertEqual(len(resp.data["actions"]), 1)
        self.assertEqual(AutomationRule.objects.count(), 1)

    def test_create_rule_with_conditions(self):
        payload = self._create_payload(conditions=[
            {"condition_type": ConditionType.PRIORITY_EQUALS, "config": {"priority": "high"}},
        ])
        resp = self.client.post(self.url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(resp.data["conditions"]), 1)

    def test_create_rule_missing_actions(self):
        payload = self._create_payload(actions=[])
        resp = self.client.post(self.url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_rule_missing_name(self):
        payload = self._create_payload()
        del payload["name"]
        resp = self.client.post(self.url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_rule_invalid_trigger(self):
        payload = self._create_payload(trigger_type="invalid_trigger")
        resp = self.client.post(self.url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_outsider_cannot_see_rules(self):
        self.client.force_authenticate(user=self.other)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_outsider_cannot_create_rule(self):
        self.client.force_authenticate(user=self.other)
        resp = self.client.post(self.url, self._create_payload(), format="json")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_unauthenticated(self):
        self.client.force_authenticate(user=None)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_nonexistent_board(self):
        resp = self.client.get("/boards/9999/automations/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)


class RuleDetailTests(AutomationTestMixin, APITestCase):
    def setUp(self):
        super().setUp()
        self.client.force_authenticate(user=self.user)
        self.rule = AutomationRule.objects.create(
            board=self.board, created_by=self.user,
            name="R1", trigger_type=TriggerType.TASK_CREATED,
        )
        RuleAction.objects.create(
            rule=self.rule, action_type=ActionType.SET_PRIORITY,
            config={"priority": "high"}, order=0,
        )
        self.url = f"/boards/{self.board.pk}/automations/{self.rule.pk}/"

    def test_get_rule(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["name"], "R1")

    def test_get_nonexistent_rule(self):
        resp = self.client.get(f"/boards/{self.board.pk}/automations/9999/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_patch_name(self):
        resp = self.client.patch(self.url, {"name": "Updated"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["name"], "Updated")

    def test_patch_trigger_type(self):
        resp = self.client.patch(self.url, {"trigger_type": TriggerType.PRIORITY_SET}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["trigger_type"], TriggerType.PRIORITY_SET)

    def test_patch_trigger_config(self):
        resp = self.client.patch(self.url, {"trigger_config": {"priority": "urgent"}}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["trigger_config"], {"priority": "urgent"})

    def test_patch_is_active(self):
        resp = self.client.patch(self.url, {"is_active": False}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertFalse(resp.data["is_active"])

    def test_patch_conditions_replaces(self):
        RuleCondition.objects.create(
            rule=self.rule, condition_type=ConditionType.PRIORITY_EQUALS,
            config={"priority": "low"},
        )
        resp = self.client.patch(self.url, {
            "conditions": [
                {"condition_type": ConditionType.LABEL_SET, "config": {"label_id": 1}},
            ],
        }, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data["conditions"]), 1)
        self.assertEqual(resp.data["conditions"][0]["condition_type"], ConditionType.LABEL_SET)

    def test_patch_actions_replaces(self):
        resp = self.client.patch(self.url, {
            "actions": [
                {"action_type": ActionType.MOVE_TO_COLUMN, "config": {"column_id": self.col2.pk}},
            ],
        }, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data["actions"]), 1)
        self.assertEqual(resp.data["actions"][0]["action_type"], ActionType.MOVE_TO_COLUMN)

    def test_patch_invalid_data(self):
        resp = self.client.patch(self.url, {"trigger_type": "invalid"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_rule(self):
        resp = self.client.delete(self.url)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(AutomationRule.objects.count(), 0)

    def test_outsider_cannot_get(self):
        self.client.force_authenticate(user=self.other)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_outsider_cannot_patch(self):
        self.client.force_authenticate(user=self.other)
        resp = self.client.patch(self.url, {"name": "Hacked"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_outsider_cannot_delete(self):
        self.client.force_authenticate(user=self.other)
        resp = self.client.delete(self.url)
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)


class RuleToggleTests(AutomationTestMixin, APITestCase):
    def setUp(self):
        super().setUp()
        self.client.force_authenticate(user=self.user)
        self.rule = AutomationRule.objects.create(
            board=self.board, created_by=self.user,
            name="Toggle Rule", trigger_type=TriggerType.TASK_CREATED,
            is_active=True,
        )
        self.url = f"/boards/{self.board.pk}/automations/{self.rule.pk}/toggle/"

    def test_toggle_deactivates(self):
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertFalse(resp.data["is_active"])

    def test_toggle_activates(self):
        self.rule.is_active = False
        self.rule.save()
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data["is_active"])

    def test_toggle_nonexistent_rule(self):
        resp = self.client.post(f"/boards/{self.board.pk}/automations/9999/toggle/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_outsider_cannot_toggle(self):
        self.client.force_authenticate(user=self.other)
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)


class AutomationLogsTests(AutomationTestMixin, APITestCase):
    def setUp(self):
        super().setUp()
        self.client.force_authenticate(user=self.user)
        self.rule = AutomationRule.objects.create(
            board=self.board, created_by=self.user,
            name="Log Rule", trigger_type=TriggerType.TASK_CREATED,
        )
        self.url = f"/boards/{self.board.pk}/automations/logs/"

    def test_logs_empty(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data, [])

    def test_logs_returns_entries(self):
        AutomationLog.objects.create(
            rule=self.rule, task=self.task, board=self.board,
            trigger_type=TriggerType.TASK_CREATED,
            actions_executed=[ActionType.SET_PRIORITY],
        )
        resp = self.client.get(self.url)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]["rule_name"], "Log Rule")
        self.assertEqual(resp.data[0]["task_title"], "Test Task")

    def test_outsider_cannot_see_logs(self):
        self.client.force_authenticate(user=self.other)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)


# ---------------------------------------------------------------------------
# Condition Tests
# ---------------------------------------------------------------------------

class ConditionTests(AutomationTestMixin, APITestCase):
    def setUp(self):
        super().setUp()
        self.rule = AutomationRule.objects.create(
            board=self.board, created_by=self.user,
            name="Cond Rule", trigger_type=TriggerType.TASK_CREATED,
        )

    def test_priority_equals_true(self):
        self.task.priority = "high"
        self.task.save()
        cond = RuleCondition.objects.create(
            rule=self.rule, condition_type=ConditionType.PRIORITY_EQUALS,
            config={"priority": "high"},
        )
        self.assertTrue(check_condition(cond, self.task))

    def test_priority_equals_false(self):
        self.task.priority = "low"
        self.task.save()
        cond = RuleCondition.objects.create(
            rule=self.rule, condition_type=ConditionType.PRIORITY_EQUALS,
            config={"priority": "high"},
        )
        self.assertFalse(check_condition(cond, self.task))

    def test_label_set_true(self):
        label = Label.objects.create(board=self.board, name="Bug", color="#ff0000")
        self.task.labels.add(label)
        cond = RuleCondition.objects.create(
            rule=self.rule, condition_type=ConditionType.LABEL_SET,
            config={"label_id": label.pk},
        )
        self.assertTrue(check_condition(cond, self.task))

    def test_label_set_false(self):
        label = Label.objects.create(board=self.board, name="Bug", color="#ff0000")
        cond = RuleCondition.objects.create(
            rule=self.rule, condition_type=ConditionType.LABEL_SET,
            config={"label_id": label.pk},
        )
        self.assertFalse(check_condition(cond, self.task))

    def test_label_set_missing_config(self):
        cond = RuleCondition.objects.create(
            rule=self.rule, condition_type=ConditionType.LABEL_SET,
            config={},
        )
        self.assertFalse(check_condition(cond, self.task))

    def test_assignee_equals_true(self):
        contact = Contact.objects.create(
            owner=self.user, first_name="John", last_name="Doe", email="john@example.com",
        )
        self.task.assignees.add(contact)
        cond = RuleCondition.objects.create(
            rule=self.rule, condition_type=ConditionType.ASSIGNEE_EQUALS,
            config={"assignee_id": contact.pk},
        )
        self.assertTrue(check_condition(cond, self.task))

    def test_assignee_equals_false(self):
        contact = Contact.objects.create(
            owner=self.user, first_name="John", last_name="Doe", email="john@example.com",
        )
        cond = RuleCondition.objects.create(
            rule=self.rule, condition_type=ConditionType.ASSIGNEE_EQUALS,
            config={"assignee_id": contact.pk},
        )
        self.assertFalse(check_condition(cond, self.task))

    def test_assignee_equals_missing_config(self):
        cond = RuleCondition.objects.create(
            rule=self.rule, condition_type=ConditionType.ASSIGNEE_EQUALS,
            config={},
        )
        self.assertFalse(check_condition(cond, self.task))

    def test_unknown_condition_type(self):
        cond = RuleCondition(
            rule=self.rule, condition_type="nonexistent_type",
            config={},
        )
        self.assertFalse(check_condition(cond, self.task))


# ---------------------------------------------------------------------------
# Action Tests
# ---------------------------------------------------------------------------

class ActionTests(AutomationTestMixin, APITestCase):
    def setUp(self):
        super().setUp()
        self.rule = AutomationRule.objects.create(
            board=self.board, created_by=self.user,
            name="Action Rule", trigger_type=TriggerType.TASK_CREATED,
        )

    @patch("automations_api.actions.send_board_event")
    def test_move_to_column(self, mock_ws):
        action = RuleAction.objects.create(
            rule=self.rule, action_type=ActionType.MOVE_TO_COLUMN,
            config={"column_id": self.col2.pk}, order=0,
        )
        from .actions import execute_action
        result = execute_action(action, self.task, self.user)
        self.assertTrue(result)
        self.task.refresh_from_db()
        self.assertEqual(self.task.column_id, self.col2.pk)
        mock_ws.assert_called()

    @patch("automations_api.actions.send_board_event")
    def test_move_to_column_same_column_noop(self, mock_ws):
        self.task.column = self.col1
        self.task.save()
        action = RuleAction.objects.create(
            rule=self.rule, action_type=ActionType.MOVE_TO_COLUMN,
            config={"column_id": self.col1.pk}, order=0,
        )
        from .actions import execute_action
        result = execute_action(action, self.task, self.user)
        self.assertTrue(result)
        mock_ws.assert_not_called()

    @patch("automations_api.actions.send_board_event")
    def test_move_to_column_missing_config(self, mock_ws):
        action = RuleAction.objects.create(
            rule=self.rule, action_type=ActionType.MOVE_TO_COLUMN,
            config={}, order=0,
        )
        from .actions import execute_action
        result = execute_action(action, self.task, self.user)
        self.assertTrue(result)
        mock_ws.assert_not_called()

    @patch("automations_api.actions.send_board_event")
    def test_set_priority(self, mock_ws):
        action = RuleAction.objects.create(
            rule=self.rule, action_type=ActionType.SET_PRIORITY,
            config={"priority": "urgent"}, order=0,
        )
        from .actions import execute_action
        result = execute_action(action, self.task, self.user)
        self.assertTrue(result)
        self.task.refresh_from_db()
        self.assertEqual(self.task.priority, "urgent")

    @patch("automations_api.actions.send_board_event")
    def test_set_priority_same_noop(self, mock_ws):
        self.task.priority = "high"
        self.task.save()
        action = RuleAction.objects.create(
            rule=self.rule, action_type=ActionType.SET_PRIORITY,
            config={"priority": "high"}, order=0,
        )
        from .actions import execute_action
        result = execute_action(action, self.task, self.user)
        self.assertTrue(result)
        mock_ws.assert_not_called()

    @patch("automations_api.actions.send_board_event")
    def test_set_priority_missing_config(self, mock_ws):
        action = RuleAction.objects.create(
            rule=self.rule, action_type=ActionType.SET_PRIORITY,
            config={}, order=0,
        )
        from .actions import execute_action
        result = execute_action(action, self.task, self.user)
        self.assertTrue(result)
        mock_ws.assert_not_called()

    @patch("automations_api.actions.send_board_event")
    def test_assign_user(self, mock_ws):
        contact = Contact.objects.create(
            owner=self.user, first_name="Jane", last_name="Doe", email="jane@example.com",
        )
        action = RuleAction.objects.create(
            rule=self.rule, action_type=ActionType.ASSIGN_USER,
            config={"assignee_id": contact.pk}, order=0,
        )
        from .actions import execute_action
        result = execute_action(action, self.task, self.user)
        self.assertTrue(result)
        self.assertTrue(self.task.assignees.filter(pk=contact.pk).exists())

    @patch("automations_api.actions.send_board_event")
    def test_assign_user_missing_config(self, mock_ws):
        action = RuleAction.objects.create(
            rule=self.rule, action_type=ActionType.ASSIGN_USER,
            config={}, order=0,
        )
        from .actions import execute_action
        result = execute_action(action, self.task, self.user)
        self.assertTrue(result)
        mock_ws.assert_not_called()

    @patch("automations_api.actions.send_board_event")
    def test_set_label(self, mock_ws):
        label = Label.objects.create(board=self.board, name="Feature", color="#00ff00")
        action = RuleAction.objects.create(
            rule=self.rule, action_type=ActionType.SET_LABEL,
            config={"label_id": label.pk}, order=0,
        )
        from .actions import execute_action
        result = execute_action(action, self.task, self.user)
        self.assertTrue(result)
        self.assertTrue(self.task.labels.filter(pk=label.pk).exists())

    @patch("automations_api.actions.send_board_event")
    def test_set_label_missing_config(self, mock_ws):
        action = RuleAction.objects.create(
            rule=self.rule, action_type=ActionType.SET_LABEL,
            config={}, order=0,
        )
        from .actions import execute_action
        result = execute_action(action, self.task, self.user)
        self.assertTrue(result)
        mock_ws.assert_not_called()

    @patch("automations_api.actions.send_board_event")
    def test_remove_label(self, mock_ws):
        label = Label.objects.create(board=self.board, name="Bug", color="#ff0000")
        self.task.labels.add(label)
        action = RuleAction.objects.create(
            rule=self.rule, action_type=ActionType.REMOVE_LABEL,
            config={"label_id": label.pk}, order=0,
        )
        from .actions import execute_action
        result = execute_action(action, self.task, self.user)
        self.assertTrue(result)
        self.assertFalse(self.task.labels.filter(pk=label.pk).exists())

    @patch("automations_api.actions.send_board_event")
    def test_remove_label_missing_config(self, mock_ws):
        action = RuleAction.objects.create(
            rule=self.rule, action_type=ActionType.REMOVE_LABEL,
            config={}, order=0,
        )
        from .actions import execute_action
        result = execute_action(action, self.task, self.user)
        self.assertTrue(result)
        mock_ws.assert_not_called()

    @patch("automations_api.actions.create_notification")
    def test_notify_creator(self, mock_notify):
        action = RuleAction.objects.create(
            rule=self.rule, action_type=ActionType.NOTIFY_CREATOR,
            config={}, order=0,
        )
        from .actions import execute_action
        result = execute_action(action, self.task, self.user)
        self.assertTrue(result)
        mock_notify.assert_called_once()

    @patch("automations_api.actions.create_notification")
    def test_notify_user(self, mock_notify):
        target = User.objects.create_user(email="target@example.com", password="pass")
        action = RuleAction.objects.create(
            rule=self.rule, action_type=ActionType.NOTIFY_USER,
            config={"user_id": target.pk}, order=0,
        )
        from .actions import execute_action
        result = execute_action(action, self.task, self.user)
        self.assertTrue(result)
        mock_notify.assert_called_once()

    @patch("automations_api.actions.create_notification")
    def test_notify_user_missing_config(self, mock_notify):
        action = RuleAction.objects.create(
            rule=self.rule, action_type=ActionType.NOTIFY_USER,
            config={}, order=0,
        )
        from .actions import execute_action
        result = execute_action(action, self.task, self.user)
        self.assertTrue(result)
        mock_notify.assert_not_called()

    @patch("automations_api.actions.create_notification")
    def test_notify_user_nonexistent(self, mock_notify):
        action = RuleAction.objects.create(
            rule=self.rule, action_type=ActionType.NOTIFY_USER,
            config={"user_id": 9999}, order=0,
        )
        from .actions import execute_action
        result = execute_action(action, self.task, self.user)
        self.assertTrue(result)
        mock_notify.assert_not_called()

    def test_unknown_action_type(self):
        action = RuleAction(
            rule=self.rule, action_type="nonexistent_action",
            config={}, order=0,
        )
        from .actions import execute_action
        result = execute_action(action, self.task, self.user)
        self.assertFalse(result)

    @patch("automations_api.actions.send_board_event")
    def test_action_exception_returns_false(self, mock_ws):
        mock_ws.side_effect = Exception("boom")
        action = RuleAction.objects.create(
            rule=self.rule, action_type=ActionType.SET_PRIORITY,
            config={"priority": "urgent"}, order=0,
        )
        from .actions import execute_action
        result = execute_action(action, self.task, self.user)
        self.assertFalse(result)


# ---------------------------------------------------------------------------
# Engine Tests
# ---------------------------------------------------------------------------

class TriggerMatchTests(AutomationTestMixin, APITestCase):
    def setUp(self):
        super().setUp()

    def _make_rule(self, trigger_type, trigger_config=None):
        return AutomationRule.objects.create(
            board=self.board, created_by=self.user,
            name="Trigger Rule", trigger_type=trigger_type,
            trigger_config=trigger_config or {},
        )

    def test_empty_config_always_matches(self):
        rule = self._make_rule(TriggerType.TASK_CREATED, {})
        self.assertTrue(_trigger_matches(rule, {}))

    def test_task_moved_to_column_matches(self):
        rule = self._make_rule(TriggerType.TASK_MOVED_TO_COLUMN, {"column_id": self.col2.pk})
        self.assertTrue(_trigger_matches(rule, {"column_id": self.col2.pk}))

    def test_task_moved_to_column_no_match(self):
        rule = self._make_rule(TriggerType.TASK_MOVED_TO_COLUMN, {"column_id": self.col2.pk})
        self.assertFalse(_trigger_matches(rule, {"column_id": self.col1.pk}))

    def test_priority_set_matches(self):
        rule = self._make_rule(TriggerType.PRIORITY_SET, {"priority": "urgent"})
        self.assertTrue(_trigger_matches(rule, {"priority": "urgent"}))

    def test_priority_set_no_match(self):
        rule = self._make_rule(TriggerType.PRIORITY_SET, {"priority": "urgent"})
        self.assertFalse(_trigger_matches(rule, {"priority": "low"}))

    def test_label_added_matches(self):
        rule = self._make_rule(TriggerType.LABEL_ADDED, {"label_id": 42})
        self.assertTrue(_trigger_matches(rule, {"label_id": 42}))

    def test_label_added_no_match(self):
        rule = self._make_rule(TriggerType.LABEL_ADDED, {"label_id": 42})
        self.assertFalse(_trigger_matches(rule, {"label_id": 99}))

    def test_deadline_approaching_always_matches(self):
        rule = self._make_rule(TriggerType.DEADLINE_APPROACHING, {"days": 3})
        self.assertTrue(_trigger_matches(rule, {}))

    def test_unknown_trigger_with_config_matches(self):
        rule = self._make_rule(TriggerType.ALL_SUBTASKS_DONE, {"some": "thing"})
        self.assertTrue(_trigger_matches(rule, {}))


class EvaluateRulesTests(AutomationTestMixin, APITestCase):
    def setUp(self):
        super().setUp()

    @patch("boards_api.ws_events.send_board_event")
    def test_evaluate_executes_matching_rule(self, mock_ws):
        rule = AutomationRule.objects.create(
            board=self.board, created_by=self.user,
            name="Auto Move", trigger_type=TriggerType.TASK_CREATED,
            is_active=True,
        )
        RuleAction.objects.create(
            rule=rule, action_type=ActionType.SET_PRIORITY,
            config={"priority": "high"}, order=0,
        )
        evaluate_rules(self.task, TriggerType.TASK_CREATED)
        self.task.refresh_from_db()
        self.assertEqual(self.task.priority, "high")
        self.assertEqual(AutomationLog.objects.count(), 1)

    @patch("boards_api.ws_events.send_board_event")
    def test_evaluate_skips_inactive_rule(self, mock_ws):
        rule = AutomationRule.objects.create(
            board=self.board, created_by=self.user,
            name="Inactive", trigger_type=TriggerType.TASK_CREATED,
            is_active=False,
        )
        RuleAction.objects.create(
            rule=rule, action_type=ActionType.SET_PRIORITY,
            config={"priority": "high"}, order=0,
        )
        evaluate_rules(self.task, TriggerType.TASK_CREATED)
        self.task.refresh_from_db()
        self.assertEqual(self.task.priority, "medium")
        self.assertEqual(AutomationLog.objects.count(), 0)

    @patch("boards_api.ws_events.send_board_event")
    def test_evaluate_skips_wrong_trigger(self, mock_ws):
        rule = AutomationRule.objects.create(
            board=self.board, created_by=self.user,
            name="Wrong", trigger_type=TriggerType.PRIORITY_SET,
            is_active=True,
        )
        RuleAction.objects.create(
            rule=rule, action_type=ActionType.SET_PRIORITY,
            config={"priority": "high"}, order=0,
        )
        evaluate_rules(self.task, TriggerType.TASK_CREATED)
        self.task.refresh_from_db()
        self.assertEqual(self.task.priority, "medium")

    @patch("boards_api.ws_events.send_board_event")
    def test_evaluate_skips_failed_condition(self, mock_ws):
        self.task.priority = "low"
        self.task.save()
        rule = AutomationRule.objects.create(
            board=self.board, created_by=self.user,
            name="Condition", trigger_type=TriggerType.TASK_CREATED,
            is_active=True,
        )
        RuleCondition.objects.create(
            rule=rule, condition_type=ConditionType.PRIORITY_EQUALS,
            config={"priority": "high"},
        )
        RuleAction.objects.create(
            rule=rule, action_type=ActionType.MOVE_TO_COLUMN,
            config={"column_id": self.col2.pk}, order=0,
        )
        evaluate_rules(self.task, TriggerType.TASK_CREATED)
        self.task.refresh_from_db()
        self.assertEqual(self.task.column_id, self.col1.pk)

    @patch("boards_api.ws_events.send_board_event")
    def test_evaluate_with_trigger_config_match(self, mock_ws):
        rule = AutomationRule.objects.create(
            board=self.board, created_by=self.user,
            name="Column Move", trigger_type=TriggerType.TASK_MOVED_TO_COLUMN,
            trigger_config={"column_id": self.col2.pk},
            is_active=True,
        )
        RuleAction.objects.create(
            rule=rule, action_type=ActionType.SET_PRIORITY,
            config={"priority": "urgent"}, order=0,
        )
        evaluate_rules(self.task, TriggerType.TASK_MOVED_TO_COLUMN, {"column_id": self.col2.pk})
        self.task.refresh_from_db()
        self.assertEqual(self.task.priority, "urgent")

    @patch("boards_api.ws_events.send_board_event")
    def test_evaluate_with_trigger_config_no_match(self, mock_ws):
        rule = AutomationRule.objects.create(
            board=self.board, created_by=self.user,
            name="Column Move", trigger_type=TriggerType.TASK_MOVED_TO_COLUMN,
            trigger_config={"column_id": self.col2.pk},
            is_active=True,
        )
        RuleAction.objects.create(
            rule=rule, action_type=ActionType.SET_PRIORITY,
            config={"priority": "urgent"}, order=0,
        )
        evaluate_rules(self.task, TriggerType.TASK_MOVED_TO_COLUMN, {"column_id": self.col1.pk})
        self.task.refresh_from_db()
        self.assertEqual(self.task.priority, "medium")

    @patch("boards_api.ws_events.send_board_event")
    def test_loop_guard_prevents_reentry(self, mock_ws):
        rule = AutomationRule.objects.create(
            board=self.board, created_by=self.user,
            name="Loop", trigger_type=TriggerType.TASK_CREATED,
            is_active=True,
        )
        RuleAction.objects.create(
            rule=rule, action_type=ActionType.SET_PRIORITY,
            config={"priority": "high"}, order=0,
        )
        from .engine import _loop_guard
        if not hasattr(_loop_guard, "active"):
            _loop_guard.active = set()
        _loop_guard.active.add((rule.pk, self.task.pk))
        try:
            evaluate_rules(self.task, TriggerType.TASK_CREATED)
            self.task.refresh_from_db()
            self.assertEqual(self.task.priority, "medium")
        finally:
            _loop_guard.active.discard((rule.pk, self.task.pk))


class ModelsQTests(AutomationTestMixin, APITestCase):
    def setUp(self):
        super().setUp()

    def test_board_or_global_filter(self):
        AutomationRule.objects.create(
            board=self.board, created_by=self.user,
            name="Board Rule", trigger_type=TriggerType.TASK_CREATED,
        )
        AutomationRule.objects.create(
            board=None, created_by=self.user,
            name="Global Rule", trigger_type=TriggerType.TASK_CREATED,
        )
        other_board = Board.objects.create(title="Other", created_by=self.other)
        AutomationRule.objects.create(
            board=other_board, created_by=self.other,
            name="Other Board Rule", trigger_type=TriggerType.TASK_CREATED,
        )
        q = models_q_board_or_global(self.board.pk)
        rules = AutomationRule.objects.filter(q)
        names = set(rules.values_list("name", flat=True))
        self.assertIn("Board Rule", names)
        self.assertIn("Global Rule", names)
        self.assertNotIn("Other Board Rule", names)


# ---------------------------------------------------------------------------
# Permission Tests — viewer cannot create/modify rules
# ---------------------------------------------------------------------------

class ViewerPermissionTests(AutomationTestMixin, APITestCase):
    def setUp(self):
        super().setUp()
        from boards_api.models import BoardMember
        self.viewer = User.objects.create_user(email="viewer@example.com", password="pass")
        BoardMember.objects.create(board=self.board, user=self.viewer, role="viewer")
        self.rule = AutomationRule.objects.create(
            board=self.board, created_by=self.user,
            name="Rule", trigger_type=TriggerType.TASK_CREATED,
        )
        RuleAction.objects.create(
            rule=self.rule, action_type=ActionType.SET_PRIORITY,
            config={"priority": "high"}, order=0,
        )
        self.client.force_authenticate(user=self.viewer)

    def test_viewer_can_list_rules(self):
        resp = self.client.get(f"/boards/{self.board.pk}/automations/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_viewer_can_get_rule(self):
        resp = self.client.get(f"/boards/{self.board.pk}/automations/{self.rule.pk}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_viewer_cannot_create_rule(self):
        resp = self.client.post(f"/boards/{self.board.pk}/automations/", {
            "name": "New",
            "trigger_type": TriggerType.TASK_CREATED,
            "actions": [{"action_type": ActionType.SET_PRIORITY, "config": {"priority": "low"}}],
        }, format="json")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_viewer_cannot_patch_rule(self):
        resp = self.client.patch(
            f"/boards/{self.board.pk}/automations/{self.rule.pk}/",
            {"name": "Hacked"}, format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_viewer_cannot_delete_rule(self):
        resp = self.client.delete(f"/boards/{self.board.pk}/automations/{self.rule.pk}/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_viewer_cannot_toggle_rule(self):
        resp = self.client.post(f"/boards/{self.board.pk}/automations/{self.rule.pk}/toggle/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
