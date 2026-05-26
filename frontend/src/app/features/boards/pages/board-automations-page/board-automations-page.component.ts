import { ChangeDetectionStrategy, Component, inject, signal, OnInit } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { RouterModule } from '@angular/router';
import { DatePipe } from '@angular/common';
import { TranslateModule, TranslateService } from '@ngx-translate/core';
import { BoardsApiService, BoardMember } from '../../../../core/boards/boards-api.service';
import { ColumnsApiService, Column } from '../../../../core/columns/columns-api.service';
import { LabelsApiService, Label } from '../../../../core/tasks/labels-api.service';
import {
  AutomationsApiService,
  AutomationRule,
  AutomationLog,
  CreateRulePayload,
} from '../../../../core/automations/automations-api.service';
import { ConfirmDialogComponent } from '../../../../shared/components/confirm-dialog/confirm-dialog.component';
import { AutomationRuleDialogComponent } from '../../components/automation-rule-dialog/automation-rule-dialog.component';
import { ToastService } from '../../../../shared/services/toast.service';
import { initBoardPage } from '../../utils/board-page-init';

@Component({
  selector: 'app-board-automations-page',
  standalone: true,
  imports: [RouterModule, DatePipe, TranslateModule, ConfirmDialogComponent, AutomationRuleDialogComponent],
  templateUrl: './board-automations-page.component.html',
  styleUrl: './board-automations-page.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class BoardAutomationsPageComponent implements OnInit {
  protected readonly board = initBoardPage();
  private readonly boardsApi = inject(BoardsApiService);
  private readonly columnsApi = inject(ColumnsApiService);
  private readonly labelsApi = inject(LabelsApiService);
  private readonly automationsApi = inject(AutomationsApiService);
  private readonly toast = inject(ToastService);
  private readonly translate = inject(TranslateService);

  loading = signal(true);
  activeTab = signal<'rules' | 'logs'>('rules');
  rules = signal<AutomationRule[]>([]);
  logs = signal<AutomationLog[]>([]);
  columns = signal<Column[]>([]);
  members = signal<BoardMember[]>([]);
  labels = signal<Label[]>([]);

  showRuleDialog = signal(false);
  editingRule = signal<AutomationRule | null>(null);
  pendingDeleteRuleId = signal<number | null>(null);

  readonly triggerLabels: Record<string, string> = {
    task_moved_to_column: 'AUTOMATIONS.TRIGGER_TASK_MOVED',
    task_created: 'AUTOMATIONS.TRIGGER_TASK_CREATED',
    priority_set: 'AUTOMATIONS.TRIGGER_PRIORITY_SET',
    all_subtasks_done: 'AUTOMATIONS.TRIGGER_SUBTASKS_DONE',
    deadline_approaching: 'AUTOMATIONS.TRIGGER_DEADLINE',
    label_added: 'AUTOMATIONS.TRIGGER_LABEL_ADDED',
  };

  readonly actionLabels: Record<string, string> = {
    move_to_column: 'AUTOMATIONS.ACTION_MOVE',
    set_priority: 'AUTOMATIONS.ACTION_PRIORITY',
    assign_user: 'AUTOMATIONS.ACTION_ASSIGN',
    set_label: 'AUTOMATIONS.ACTION_SET_LABEL',
    remove_label: 'AUTOMATIONS.ACTION_REMOVE_LABEL',
    notify_creator: 'AUTOMATIONS.ACTION_NOTIFY_CREATOR',
    notify_assignees: 'AUTOMATIONS.ACTION_NOTIFY_ASSIGNEES',
    notify_user: 'AUTOMATIONS.ACTION_NOTIFY_USER',
  };

  ngOnInit(): void {
    this.columnsApi.getByBoard(this.board.boardId())
      .pipe(takeUntilDestroyed(this.board.destroyRef))
      .subscribe({ next: c => this.columns.set(c) });

    this.boardsApi.getMembers(this.board.boardId())
      .pipe(takeUntilDestroyed(this.board.destroyRef))
      .subscribe({ next: m => this.members.set(m) });

    this.labelsApi.getByBoard(this.board.boardId())
      .pipe(takeUntilDestroyed(this.board.destroyRef))
      .subscribe({ next: l => this.labels.set(l) });

    this.loadRules();
    this.loadLogs();
  }

  loadRules(): void {
    this.automationsApi.getByBoard(this.board.boardId())
      .pipe(takeUntilDestroyed(this.board.destroyRef))
      .subscribe({
        next: rules => {
          this.rules.set(rules);
          this.loading.set(false);
        },
      });
  }

  loadLogs(): void {
    this.automationsApi.getLogs(this.board.boardId())
      .pipe(takeUntilDestroyed(this.board.destroyRef))
      .subscribe({ next: logs => this.logs.set(logs) });
  }

  toggleRule(rule: AutomationRule): void {
    this.automationsApi.toggle(this.board.boardId(), rule.id)
      .pipe(takeUntilDestroyed(this.board.destroyRef))
      .subscribe({
        next: updated => this.rules.update(r => r.map(x => x.id === updated.id ? updated : x)),
      });
  }

  openCreateDialog(): void {
    this.editingRule.set(null);
    this.showRuleDialog.set(true);
  }

  openEditDialog(rule: AutomationRule): void {
    this.editingRule.set(rule);
    this.showRuleDialog.set(true);
  }

  onRuleSaved(payload: CreateRulePayload): void {
    const editing = this.editingRule();
    if (editing) {
      this.automationsApi.patch(this.board.boardId(), editing.id, payload)
        .pipe(takeUntilDestroyed(this.board.destroyRef))
        .subscribe({
          next: updated => {
            this.rules.update(r => r.map(x => x.id === updated.id ? updated : x));
            this.showRuleDialog.set(false);
            this.toast.show(this.translate.instant('TOAST.RULE_UPDATED'));
          },
        });
    } else {
      this.automationsApi.create(this.board.boardId(), payload)
        .pipe(takeUntilDestroyed(this.board.destroyRef))
        .subscribe({
          next: created => {
            this.rules.update(r => [...r, created]);
            this.showRuleDialog.set(false);
            this.toast.show(this.translate.instant('TOAST.RULE_CREATED'));
          },
        });
    }
  }

  confirmDeleteRule(): void {
    const id = this.pendingDeleteRuleId();
    if (id === null) return;
    this.pendingDeleteRuleId.set(null);
    this.automationsApi.delete(this.board.boardId(), id)
      .pipe(takeUntilDestroyed(this.board.destroyRef))
      .subscribe({
        next: () => {
          this.rules.update(r => r.filter(x => x.id !== id));
          this.toast.show(this.translate.instant('TOAST.RULE_DELETED'));
        },
      });
  }

  actionSummary(rule: AutomationRule): string {
    return rule.actions
      .map(a => this.translate.instant(this.actionLabels[a.action_type] ?? a.action_type))
      .join(', ');
  }

  logActionSummary(actions: string[]): string {
    return actions
      .map(a => this.translate.instant(this.actionLabels[a] ?? a))
      .join(', ');
  }
}
