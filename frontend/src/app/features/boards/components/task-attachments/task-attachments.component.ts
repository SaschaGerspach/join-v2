import { Component, DestroyRef, inject, input, signal, OnInit } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { Attachment, AttachmentsApiService } from '../../../../core/tasks/attachments-api.service';
import { ToastService } from '../../../../shared/services/toast.service';

@Component({
  selector: 'app-task-attachments',
  standalone: true,
  templateUrl: './task-attachments.component.html',
  styleUrl: './task-attachments.component.scss',
})
export class TaskAttachmentsComponent implements OnInit {
  private readonly attachmentsApi = inject(AttachmentsApiService);
  private readonly toast = inject(ToastService);
  private readonly destroyRef = inject(DestroyRef);

  taskId = input.required<number>();

  attachments = signal<Attachment[]>([]);

  private readonly allowedExtensions = new Set([
    'png', 'jpg', 'jpeg', 'gif', 'webp',
    'pdf', 'txt', 'md', 'csv',
    'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx',
    'zip',
  ]);

  ngOnInit(): void {
    this.attachmentsApi.getByTask(this.taskId())
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe(atts => this.attachments.set(atts));
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
    this.attachmentsApi.upload(this.taskId(), file)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: att => this.attachments.update(list => [...list, att]),
        error: () => this.toast.show('Failed to upload file.', 'error'),
      });
    input.value = '';
  }

  deleteAttachment(att: Attachment): void {
    this.attachmentsApi.delete(this.taskId(), att.id)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: () => this.attachments.update(list => list.filter(a => a.id !== att.id)),
        error: () => this.toast.show('Failed to delete file.', 'error'),
      });
  }

  formatSize(bytes: number): string {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
  }
}
