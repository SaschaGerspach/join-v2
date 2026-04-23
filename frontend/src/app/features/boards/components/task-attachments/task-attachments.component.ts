import { ChangeDetectionStrategy, Component, DestroyRef, inject, input, signal, computed, OnInit } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';
import { TranslateModule } from '@ngx-translate/core';
import { Attachment, AttachmentsApiService } from '../../../../core/tasks/attachments-api.service';
import { ConfirmDialogComponent } from '../../../../shared/components/confirm-dialog/confirm-dialog.component';
import { ToastService } from '../../../../shared/services/toast.service';

@Component({
  selector: 'app-task-attachments',
  standalone: true,
  imports: [TranslateModule, ConfirmDialogComponent],
  templateUrl: './task-attachments.component.html',
  styleUrl: './task-attachments.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class TaskAttachmentsComponent implements OnInit {
  private readonly attachmentsApi = inject(AttachmentsApiService);
  private readonly toast = inject(ToastService);
  private readonly destroyRef = inject(DestroyRef);
  private readonly sanitizer = inject(DomSanitizer);

  taskId = input.required<number>();

  attachments = signal<Attachment[]>([]);
  pendingDeleteAttachment = signal<Attachment | null>(null);
  previewAttachment = signal<Attachment | null>(null);
  previewBlobUrl = signal<SafeResourceUrl | null>(null);

  private readonly imageExtensions = new Set(['png', 'jpg', 'jpeg', 'gif', 'webp']);

  imageAttachments = computed(() =>
    this.attachments().filter(a => this.imageExtensions.has(this.getExt(a.filename)))
  );

  fileAttachments = computed(() =>
    this.attachments().filter(a => !this.imageExtensions.has(this.getExt(a.filename)))
  );

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
    const ext = file.name.split('.').pop()?.toLowerCase() ?? '';
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
    this.pendingDeleteAttachment.set(att);
  }

  confirmDeleteAttachment(): void {
    const att = this.pendingDeleteAttachment();
    if (!att) return;
    this.pendingDeleteAttachment.set(null);
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

  openPreview(att: Attachment): void {
    this.previewAttachment.set(att);
    this.previewBlobUrl.set(null);
    if (this.isPdf(att.filename) || this.isImage(att.filename)) {
      this.attachmentsApi.download(this.taskId(), att.id)
        .pipe(takeUntilDestroyed(this.destroyRef))
        .subscribe({
          next: blob => {
            const url = URL.createObjectURL(blob);
            this.previewBlobUrl.set(this.sanitizer.bypassSecurityTrustResourceUrl(url));
          },
        });
    }
  }

  closePreview(): void {
    const url = this.previewBlobUrl();
    if (url) {
      this.previewBlobUrl.set(null);
    }
    this.previewAttachment.set(null);
  }

  downloadAttachment(att: Attachment): void {
    this.attachmentsApi.download(this.taskId(), att.id)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: blob => {
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = att.filename;
          a.click();
          URL.revokeObjectURL(url);
        },
        error: () => this.toast.show('Download failed.', 'error'),
      });
  }

  isImage(filename: string): boolean {
    return this.imageExtensions.has(this.getExt(filename));
  }

  isPdf(filename: string): boolean {
    return this.getExt(filename) === 'pdf';
  }

  private getExt(filename: string): string {
    return filename.split('.').pop()?.toLowerCase() ?? '';
  }
}
