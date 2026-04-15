import { Component, AfterViewInit, ElementRef, HostListener, inject, input, output, signal, OnInit, ViewChild } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { SlicePipe } from '@angular/common';
import { Task, TasksApiService } from '../../../../core/tasks/tasks-api.service';
import { Column } from '../../../../core/columns/columns-api.service';
import { Subtask, SubtasksApiService } from '../../../../core/tasks/subtasks-api.service';
import { Contact, ContactsApiService } from '../../../../core/contacts/contacts-api.service';
import { Comment, CommentsApiService } from '../../../../core/tasks/comments-api.service';
import { Label, LabelsApiService } from '../../../../core/tasks/labels-api.service';
import { Attachment, AttachmentsApiService } from '../../../../core/tasks/attachments-api.service';
import { ConfirmDialogComponent } from '../../../../shared/components/confirm-dialog/confirm-dialog.component';
import { ToastService } from '../../../../shared/services/toast.service';
import { AuthService } from '../../../../core/auth/auth.service';

@Component({
  selector: 'app-task-detail-modal',
  standalone: true,
  imports: [FormsModule, SlicePipe, ConfirmDialogComponent],
  templateUrl: './task-detail-modal.component.html',
  styleUrl: './task-detail-modal.component.scss',
})
export class TaskDetailModalComponent implements OnInit, AfterViewInit {
  @ViewChild('titleInput') titleInput!: ElementRef<HTMLInputElement>;
  private readonly tasksApi = inject(TasksApiService);
  private readonly subtasksApi = inject(SubtasksApiService);
  private readonly contactsApi = inject(ContactsApiService);
  private readonly commentsApi = inject(CommentsApiService);
  private readonly labelsApi = inject(LabelsApiService);
  private readonly attachmentsApi = inject(AttachmentsApiService);
  private readonly toast = inject(ToastService);
  readonly auth = inject(AuthService);

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

  comments = signal<Comment[]>([]);
  newCommentText = signal('');
  editingCommentId = signal<number | null>(null);
  editingCommentText = '';

  boardLabels = signal<Label[]>([]);
  selectedLabelIds = signal<Set<number>>(new Set());
  newLabelName = '';
  newLabelColor = '#29abe2';

  attachments = signal<Attachment[]>([]);

  private readonly allowedExtensions = new Set([
    'png', 'jpg', 'jpeg', 'gif', 'webp',
    'pdf', 'txt', 'md', 'csv',
    'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx',
    'zip',
  ]);

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
    this.commentsApi.getAll(t.id).subscribe(comments => this.comments.set(comments));
    this.labelsApi.getByBoard(t.board).subscribe(labels => this.boardLabels.set(labels));
    this.selectedLabelIds.set(new Set(t.labels?.map(l => l.id) ?? []));
    this.attachmentsApi.getByTask(t.id).subscribe(atts => this.attachments.set(atts));
  }

  save(): void {
    const payload: any = {
      title: this.title().trim(),
      description: this.description().trim(),
      priority: this.priority(),
      due_date: this.dueDate() || null,
      column: this.columnId(),
      assigned_to: this.assignedTo(),
      label_ids: [...this.selectedLabelIds()],
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

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) return;
    if (file.size > 5 * 1024 * 1024) {
      this.toast.show('File too large (max 5MB).', 'error');
      input.value = '';
      return;
    }
    const ext = file.name.includes('.') ? file.name.split('.').pop()!.toLowerCase() : '';
    if (!this.allowedExtensions.has(ext)) {
      this.toast.show('File type not allowed.', 'error');
      input.value = '';
      return;
    }
    this.attachmentsApi.upload(this.task().id, file).subscribe({
      next: att => this.attachments.update(list => [...list, att]),
      error: () => this.toast.show('Failed to upload file.', 'error'),
    });
    input.value = '';
  }

  formatSize(bytes: number): string {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
  }

  deleteAttachment(att: Attachment): void {
    this.attachmentsApi.delete(this.task().id, att.id).subscribe({
      next: () => this.attachments.update(list => list.filter(a => a.id !== att.id)),
      error: () => this.toast.show('Failed to delete file.', 'error'),
    });
  }

  toggleLabel(labelId: number): void {
    this.selectedLabelIds.update(set => {
      const next = new Set(set);
      if (next.has(labelId)) next.delete(labelId);
      else next.add(labelId);
      return next;
    });
  }

  createLabel(): void {
    const name = this.newLabelName.trim();
    if (!name) return;
    this.labelsApi.create(this.task().board, name, this.newLabelColor).subscribe({
      next: label => {
        this.boardLabels.update(l => [...l, label]);
        this.selectedLabelIds.update(s => { const n = new Set(s); n.add(label.id); return n; });
        this.newLabelName = '';
      },
      error: () => this.toast.show('Failed to create label.', 'error'),
    });
  }

  addComment(): void {
    const text = this.newCommentText().trim();
    if (!text) return;
    this.commentsApi.create(this.task().id, text).subscribe({
      next: c => { this.comments.update(list => [...list, c]); this.newCommentText.set(''); },
      error: () => this.toast.show('Failed to add comment.', 'error'),
    });
  }

  startEditComment(c: Comment): void {
    this.editingCommentId.set(c.id);
    this.editingCommentText = c.text;
  }

  confirmEditComment(c: Comment): void {
    const text = this.editingCommentText.trim();
    this.editingCommentId.set(null);
    if (!text || text === c.text) return;
    this.commentsApi.patch(this.task().id, c.id, text).subscribe({
      next: updated => this.comments.update(list => list.map(x => x.id === updated.id ? updated : x)),
      error: () => this.toast.show('Failed to edit comment.', 'error'),
    });
  }

  deleteComment(id: number): void {
    this.commentsApi.delete(this.task().id, id).subscribe({
      next: () => this.comments.update(list => list.filter(c => c.id !== id)),
      error: () => this.toast.show('Failed to delete comment.', 'error'),
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
