import {
  ChangeDetectionStrategy,
  Component,
  HostListener,
  input,
  output,
  signal,
  OnInit,
} from '@angular/core';
import { FormsModule } from '@angular/forms';
import { TranslateModule } from '@ngx-translate/core';
import { FocusTrapDirective } from '../../../../shared/directives/focus-trap.directive';
import { Column } from '../../../../core/columns/columns-api.service';
import { BoardMember } from '../../../../core/boards/boards-api.service';
import { Label } from '../../../../core/tasks/labels-api.service';
import {
  AutomationRule,
  CreateRulePayload,
  TriggerType,
  ConditionType,
  ActionType,
  RuleCondition,
  RuleAction,
} from '../../../../core/automations/automations-api.service';

@Component({
  selector: 'app-automation-rule-dialog',
  standalone: true,
  imports: [FormsModule, TranslateModule, FocusTrapDirective],
  templateUrl: './automation-rule-dialog.component.html',
  styleUrl: './automation-rule-dialog.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AutomationRuleDialogComponent implements OnInit {
  rule = input<AutomationRule | null>(null);
  columns = input.required<Column[]>();
  members = input.required<BoardMember[]>();
  labels = input.required<Label[]>();

  saved = output<CreateRulePayload>();
  cancelled = output<void>();

  name = '';
  triggerType = signal<TriggerType>('task_created');
  triggerConfig = signal<Record<string, unknown>>({});
  conditions = signal<RuleCondition[]>([]);
  actions = signal<RuleAction[]>([{ action_type: 'notify_creator', config: {}, order: 0 }]);
  submitted = false;

  readonly triggerTypes: TriggerType[] = [
    'task_created',
    'task_moved_to_column',
    'priority_set',
    'all_subtasks_done',
    'deadline_approaching',
    'label_added',
  ];

  readonly conditionTypes: ConditionType[] = [
    'priority_equals',
    'label_set',
    'assignee_equals',
  ];

  readonly actionTypes: ActionType[] = [
    'move_to_column',
    'set_priority',
    'assign_user',
    'set_label',
    'remove_label',
    'notify_creator',
    'notify_assignees',
    'notify_user',
  ];

  readonly priorities = ['urgent', 'high', 'medium', 'low'] as const;

  readonly triggerLabelMap: Record<string, string> = {
    task_moved_to_column: 'AUTOMATIONS.TRIGGER_TASK_MOVED',
    task_created: 'AUTOMATIONS.TRIGGER_TASK_CREATED',
    priority_set: 'AUTOMATIONS.TRIGGER_PRIORITY_SET',
    all_subtasks_done: 'AUTOMATIONS.TRIGGER_SUBTASKS_DONE',
    deadline_approaching: 'AUTOMATIONS.TRIGGER_DEADLINE',
    label_added: 'AUTOMATIONS.TRIGGER_LABEL_ADDED',
  };

  readonly conditionLabelMap: Record<string, string> = {
    priority_equals: 'AUTOMATIONS.CONDITION_PRIORITY',
    label_set: 'AUTOMATIONS.CONDITION_LABEL',
    assignee_equals: 'AUTOMATIONS.CONDITION_ASSIGNEE',
  };

  readonly actionLabelMap: Record<string, string> = {
    move_to_column: 'AUTOMATIONS.ACTION_MOVE',
    set_priority: 'AUTOMATIONS.ACTION_PRIORITY',
    assign_user: 'AUTOMATIONS.ACTION_ASSIGN',
    set_label: 'AUTOMATIONS.ACTION_SET_LABEL',
    remove_label: 'AUTOMATIONS.ACTION_REMOVE_LABEL',
    notify_creator: 'AUTOMATIONS.ACTION_NOTIFY_CREATOR',
    notify_assignees: 'AUTOMATIONS.ACTION_NOTIFY_ASSIGNEES',
    notify_user: 'AUTOMATIONS.ACTION_NOTIFY_USER',
  };

  @HostListener('document:keydown.escape')
  onEscape(): void {
    this.cancelled.emit();
  }

  ngOnInit(): void {
    const r = this.rule();
    if (r) {
      this.name = r.name;
      this.triggerType.set(r.trigger_type);
      this.triggerConfig.set({ ...r.trigger_config });
      this.conditions.set(r.conditions.map(c => ({ ...c, config: { ...c.config } })));
      this.actions.set(r.actions.map(a => ({ ...a, config: { ...a.config } })));
    }
  }

  needsTriggerConfig(): boolean {
    return ['task_moved_to_column', 'priority_set', 'label_added', 'deadline_approaching'].includes(this.triggerType());
  }

  onTriggerTypeChange(type: TriggerType): void {
    this.triggerType.set(type);
    this.triggerConfig.set({});
  }

  updateTriggerConfig(key: string, value: unknown): void {
    this.triggerConfig.update(c => ({ ...c, [key]: value }));
  }

  addCondition(): void {
    this.conditions.update(c => [...c, { condition_type: 'priority_equals', config: {} }]);
  }

  removeCondition(index: number): void {
    this.conditions.update(c => c.filter((_, i) => i !== index));
  }

  updateConditionType(index: number, type: ConditionType): void {
    this.conditions.update(c => c.map((cond, i) =>
      i === index ? { condition_type: type, config: {} } : cond
    ));
  }

  updateConditionConfig(index: number, key: string, value: unknown): void {
    this.conditions.update(c => c.map((cond, i) =>
      i === index ? { ...cond, config: { ...cond.config, [key]: value } } : cond
    ));
  }

  addAction(): void {
    this.actions.update(a => [...a, { action_type: 'notify_creator', config: {}, order: a.length }]);
  }

  removeAction(index: number): void {
    this.actions.update(a => a.filter((_, i) => i !== index).map((act, i) => ({ ...act, order: i })));
  }

  updateActionType(index: number, type: ActionType): void {
    this.actions.update(a => a.map((act, i) =>
      i === index ? { action_type: type, config: {}, order: act.order } : act
    ));
  }

  updateActionConfig(index: number, key: string, value: unknown): void {
    this.actions.update(a => a.map((act, i) =>
      i === index ? { ...act, config: { ...act.config, [key]: value } } : act
    ));
  }

  submit(): void {
    this.submitted = true;
    if (!this.name.trim() || this.actions().length === 0) return;

    const payload: CreateRulePayload = {
      name: this.name.trim(),
      trigger_type: this.triggerType(),
      trigger_config: Object.keys(this.triggerConfig()).length > 0 ? this.triggerConfig() : undefined,
      conditions: this.conditions().length > 0 ? this.conditions() : undefined,
      actions: this.actions(),
    };
    this.saved.emit(payload);
  }
}
