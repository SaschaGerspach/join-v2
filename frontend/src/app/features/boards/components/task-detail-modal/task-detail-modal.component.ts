import { Component, AfterViewInit, ElementRef, HostListener, inject, input, output, signal, OnInit, ViewChild } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Task, TasksApiService } from '../../../../core/tasks/tasks-api.service';
import { Column } from '../../../../core/columns/columns-api.service';
import { Subtask, SubtasksApiService } from '../../../../core/tasks/subtasks-api.service';
import { Contact, ContactsApiService } from '../../../../core/contacts/contacts-api.service';
import { ConfirmDialogComponent } from '../../../../shared/components/confirm-dialog/confirm-dialog.component';
import { ToastService } from '../../../../shared/services/toast.service';

@Component({
  selector: 'app-task-detail-modal',
  standalone: true,
  imports: [FormsModule, ConfirmDialogComponent],
  templateUrl: './task-detail-modal.component.html',
  styleUrl: './task-detail-modal.component.scss',
})
export class TaskDetailModalComponent implements OnInit, AfterViewInit {
  @ViewChild('titleInput') titleInput!: ElementRef<HTMLInputElement>;
  private readonly tasksApi = inject(TasksApiService);
  private readonly subtasksApi = inject(SubtasksApiService);
  private readonly contactsApi = inject(ContactsApiService);
  private readonly toast = inject(ToastService);

  task = input.required<Task>();
  columns = input.required<Column[]>();

  contacts = signal<Contact[]>([]);

  closed = output<void>();
  taskUpdated = output<Task>();
  taskDeleted = output<number>();

  title = signal('');
  description = signal('');
  priority = signal<'low' | 'medium' | 'high' | 'urgent'>('medium');
  dueDate = signal('');
  columnId = signal<number | null>(null);

  subtasks = signal<Subtask[]>([]);
  newSubtaskTitle = signal('');
  assignedTo = signal<number | null>(null);
  showDeleteConfirm = signal(false);
  editingSubtaskId = signal<number | null>(null);
  editingSubtaskTitle = '';

  readonly priorities = ['urgent', 'high', 'medium', 'low'] as const;

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
    this.assignedTo.set(t.assigned_to);

    this.subtasksApi.getByTask(t.id).subscribe(subs => this.subtasks.set(subs));
    this.contactsApi.getAll().subscribe(contacts => this.contacts.set(contacts));
  }

  save(): void {
    const payload = {
      title: this.title().trim(),
      description: this.description().trim(),
      priority: this.priority(),
      due_date: this.dueDate() || null,
      column: this.columnId(),
      assigned_to: this.assignedTo(),
    };

    this.tasksApi.patch(this.task().id, payload).subscribe({
      next: updated => {
        this.taskUpdated.emit(updated);
        this.closed.emit();
        this.toast.show('Task saved');
      },
      error: () => this.toast.show('Failed to save task.', 'error'),
    });
  }

  deleteTask(): void {
    this.showDeleteConfirm.set(true);
  }

  confirmDeleteTask(): void {
    this.tasksApi.delete(this.task().id).subscribe({
      next: () => {
        this.taskDeleted.emit(this.task().id);
        this.closed.emit();
      },
      error: () => this.toast.show('Failed to delete task.', 'error'),
    });
  }

  addSubtask(): void {
    const title = this.newSubtaskTitle().trim();
    if (!title) return;

    this.subtasksApi.create(this.task().id, title).subscribe({
      next: sub => {
        this.subtasks.update(s => [...s, sub]);
        this.newSubtaskTitle.set('');
        this.emitSubtaskCounts();
      },
      error: () => this.toast.show('Failed to add subtask.', 'error'),
    });
  }

  toggleSubtask(sub: Subtask): void {
    this.subtasksApi.patch(this.task().id, sub.id, { done: !sub.done }).subscribe(updated => {
      this.subtasks.update(s => s.map(x => x.id === updated.id ? updated : x));
      this.emitSubtaskCounts();
    });
  }

  deleteSubtask(sub: Subtask): void {
    this.subtasksApi.delete(this.task().id, sub.id).subscribe({
      next: () => {
        this.subtasks.update(s => s.filter(x => x.id !== sub.id));
        this.emitSubtaskCounts();
      },
      error: () => this.toast.show('Failed to delete subtask.', 'error'),
    });
  }

  startEditSubtask(sub: Subtask): void {
    this.editingSubtaskId.set(sub.id);
    this.editingSubtaskTitle = sub.title;
  }

  confirmEditSubtask(sub: Subtask): void {
    const title = this.editingSubtaskTitle.trim();
    this.editingSubtaskId.set(null);
    if (!title || title === sub.title) return;
    this.subtasksApi.patch(this.task().id, sub.id, { title }).subscribe({
      next: updated => this.subtasks.update(s => s.map(x => x.id === updated.id ? updated : x)),
      error: () => this.toast.show('Failed to rename subtask.', 'error'),
    });
  }

  private emitSubtaskCounts(): void {
    const subs = this.subtasks();
    this.taskUpdated.emit({
      ...this.task(),
      subtask_count: subs.length,
      subtask_done_count: subs.filter(s => s.done).length,
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
