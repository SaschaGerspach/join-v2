import { ChangeDetectionStrategy, Component, AfterViewInit, DestroyRef, ElementRef, HostListener, inject, input, output, signal, OnInit, ViewChild } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormsModule } from '@angular/forms';
import { Task, TasksApiService, UpdateTaskPayload, Recurrence } from '../../../../core/tasks/tasks-api.service';
import { Column } from '../../../../core/columns/columns-api.service';
import { Contact, ContactsApiService } from '../../../../core/contacts/contacts-api.service';
import { ConfirmDialogComponent } from '../../../../shared/components/confirm-dialog/confirm-dialog.component';
import { ToastService } from '../../../../shared/services/toast.service';
import { TaskSubtasksComponent } from '../task-subtasks/task-subtasks.component';
import { TaskCommentsComponent } from '../task-comments/task-comments.component';
import { TaskAttachmentsComponent } from '../task-attachments/task-attachments.component';
import { TaskLabelsComponent } from '../task-labels/task-labels.component';
import { TaskDependenciesComponent } from '../task-dependencies/task-dependencies.component';
import { TaskCustomFieldsComponent } from '../task-custom-fields/task-custom-fields.component';
import { TaskTimeTrackingComponent } from '../task-time-tracking/task-time-tracking.component';

@Component({
  selector: 'app-task-detail-modal',
  standalone: true,
  imports: [FormsModule, ConfirmDialogComponent, TaskSubtasksComponent, TaskCommentsComponent, TaskAttachmentsComponent, TaskLabelsComponent, TaskDependenciesComponent, TaskCustomFieldsComponent, TaskTimeTrackingComponent],
  templateUrl: './task-detail-modal.component.html',
  styleUrl: './task-detail-modal.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class TaskDetailModalComponent implements OnInit, AfterViewInit {
  @ViewChild('titleInput') titleInput!: ElementRef<HTMLInputElement>;
  private readonly tasksApi = inject(TasksApiService);
  private readonly contactsApi = inject(ContactsApiService);
  private readonly toast = inject(ToastService);
  private readonly destroyRef = inject(DestroyRef);

  task = input.required<Task>();
  columns = input.required<Column[]>();
  boardTasks = input.required<Task[]>();

  contacts = signal<Contact[]>([]);

  closed = output<void>();
  taskUpdated = output<Task>();
  taskDeleted = output<number>();
  taskDuplicated = output<Task>();

  title = signal('');
  description = signal('');
  priority = signal<'low' | 'medium' | 'high' | 'urgent'>('medium');
  dueDate = signal('');
  columnId = signal<number | null>(null);
  assignedTo = signal<number[]>([]);
  recurrence = signal<Recurrence>(null);
  selectedLabelIds = signal<Set<number>>(new Set());
  showDeleteConfirm = signal(false);

  readonly priorities = ['urgent', 'high', 'medium', 'low'] as const;
  readonly recurrenceOptions = [
    { value: null, label: 'None' },
    { value: 'daily', label: 'Daily' },
    { value: 'weekly', label: 'Weekly' },
    { value: 'biweekly', label: 'Biweekly' },
    { value: 'monthly', label: 'Monthly' },
  ] as const;

  ngAfterViewInit(): void {
    this.titleInput?.nativeElement.focus();
  }

  ngOnInit(): void {
    const t = this.task();
    this.title.set(t.title);
    this.description.set(t.description ?? '');
    this.priority.set(t.priority);
    this.dueDate.set(t.due_date ?? '');
    this.columnId.set(t.column);
    this.assignedTo.set(t.assigned_to ?? []);
    this.recurrence.set(t.recurrence ?? null);
    this.selectedLabelIds.set(new Set(t.labels?.map(l => l.id) ?? []));

    this.contactsApi.getAll().pipe(takeUntilDestroyed(this.destroyRef)).subscribe(contacts => this.contacts.set(contacts));
  }

  save(): void {
    const payload: UpdateTaskPayload = {
      title: this.title().trim(),
      description: this.description().trim(),
      priority: this.priority(),
      due_date: this.dueDate() || null,
      recurrence: this.recurrence(),
      column: this.columnId(),
      assigned_to: this.assignedTo(),
      label_ids: [...this.selectedLabelIds()],
    };

    this.tasksApi.patch(this.task().id, payload).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: updated => {
        this.taskUpdated.emit(updated);
        this.closed.emit();
        this.toast.show('Task saved');
      },
      error: () => this.toast.show('Failed to save task.', 'error'),
    });
  }

  toggleAssignee(id: number): void {
    const current = this.assignedTo();
    if (current.includes(id)) {
      this.assignedTo.set(current.filter(x => x !== id));
    } else {
      this.assignedTo.set([...current, id]);
    }
  }

  deleteTask(): void {
    this.showDeleteConfirm.set(true);
  }

  confirmDeleteTask(): void {
    this.tasksApi.delete(this.task().id).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: () => {
        this.taskDeleted.emit(this.task().id);
        this.closed.emit();
      },
      error: () => this.toast.show('Failed to delete task.', 'error'),
    });
  }

  duplicateTask(): void {
    this.tasksApi.duplicate(this.task().id).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: newTask => {
        this.taskDuplicated.emit(newTask);
        this.closed.emit();
        this.toast.show('Task duplicated');
      },
      error: () => this.toast.show('Failed to duplicate task.', 'error'),
    });
  }

  onSubtaskCountChanged(counts: { total: number; done: number }): void {
    this.taskUpdated.emit({
      ...this.task(),
      subtask_count: counts.total,
      subtask_done_count: counts.done,
    });
  }

  @HostListener('document:keydown.escape')
  onEscape(): void {
    if (!this.showDeleteConfirm()) {
      this.closed.emit();
    }
  }

  close(): void {
    this.closed.emit();
  }
}
