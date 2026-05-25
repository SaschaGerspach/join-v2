import { ChangeDetectionStrategy, Component, DestroyRef, inject, signal, OnInit } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { ActivatedRoute, RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { TranslateModule, TranslateService } from '@ngx-translate/core';
import { BoardsApiService } from '../../../../core/boards/boards-api.service';
import { TemplatesApiService, TaskTemplate } from '../../../../core/templates/templates-api.service';
import { ToastService } from '../../../../shared/services/toast.service';
import { ConfirmDialogComponent } from '../../../../shared/components/confirm-dialog/confirm-dialog.component';

@Component({
  selector: 'app-board-templates-page',
  standalone: true,
  imports: [RouterModule, FormsModule, TranslateModule, ConfirmDialogComponent],
  templateUrl: './board-templates-page.component.html',
  styleUrl: './board-templates-page.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class BoardTemplatesPageComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly destroyRef = inject(DestroyRef);
  private readonly boardsApi = inject(BoardsApiService);
  private readonly templatesApi = inject(TemplatesApiService);
  private readonly toast = inject(ToastService);
  private readonly translate = inject(TranslateService);

  boardId = 0;
  boardTitle = signal('Board');
  loading = signal(true);
  templates = signal<TaskTemplate[]>([]);

  showForm = signal(false);
  editingId = signal<number | null>(null);
  formName = signal('');
  formTitle = signal('');
  formDescription = signal('');
  formPriority = signal('medium');
  formSubtasks = signal<string[]>([]);
  newSubtask = signal('');
  deleteTarget = signal<number | null>(null);

  readonly priorities = ['urgent', 'high', 'medium', 'low'] as const;

  ngOnInit(): void {
    this.boardId = Number(this.route.snapshot.paramMap.get('id'));
    this.boardsApi.getById(this.boardId)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe(b => this.boardTitle.set(b.title));
    this.loadTemplates();
  }

  loadTemplates(): void {
    this.templatesApi.getByBoard(this.boardId)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe(t => {
        this.templates.set(t);
        this.loading.set(false);
      });
  }

  openCreateForm(): void {
    this.editingId.set(null);
    this.formName.set('');
    this.formTitle.set('');
    this.formDescription.set('');
    this.formPriority.set('medium');
    this.formSubtasks.set([]);
    this.newSubtask.set('');
    this.showForm.set(true);
  }

  editTemplate(t: TaskTemplate): void {
    this.editingId.set(t.id);
    this.formName.set(t.name);
    this.formTitle.set(t.title);
    this.formDescription.set(t.description);
    this.formPriority.set(t.priority);
    this.formSubtasks.set([...t.subtasks]);
    this.newSubtask.set('');
    this.showForm.set(true);
  }

  addSubtask(): void {
    const title = this.newSubtask().trim();
    if (!title) return;
    this.formSubtasks.set([...this.formSubtasks(), title]);
    this.newSubtask.set('');
  }

  removeSubtask(index: number): void {
    this.formSubtasks.set(this.formSubtasks().filter((_, i) => i !== index));
  }

  saveTemplate(): void {
    const name = this.formName().trim();
    if (!name) return;

    const payload = {
      name,
      title: this.formTitle().trim(),
      description: this.formDescription().trim(),
      priority: this.formPriority(),
      subtasks: this.formSubtasks(),
      label_ids: [] as number[],
    };

    const id = this.editingId();
    const obs = id
      ? this.templatesApi.update(id, payload)
      : this.templatesApi.create(this.boardId, payload);

    obs.pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: () => {
        this.showForm.set(false);
        this.loadTemplates();
        this.toast.show(this.translate.instant('TOAST.TEMPLATE_SAVED'));
      },
      error: () => this.toast.show(this.translate.instant('TOAST.FAILED_SAVE_TEMPLATE'), 'error'),
    });
  }

  useTemplate(t: TaskTemplate): void {
    this.templatesApi.createTask(t.id)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: () => this.toast.show(this.translate.instant('TOAST.TASK_CREATED')),
        error: () => this.toast.show(this.translate.instant('TOAST.FAILED_CREATE_TASK'), 'error'),
      });
  }

  confirmDelete(id: number): void {
    this.deleteTarget.set(id);
  }

  doDelete(): void {
    const id = this.deleteTarget();
    if (!id) return;
    this.templatesApi.delete(id)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: () => {
          this.deleteTarget.set(null);
          this.loadTemplates();
          this.toast.show(this.translate.instant('TOAST.TEMPLATE_DELETED'));
        },
        error: () => this.toast.show(this.translate.instant('TOAST.FAILED_DELETE_TEMPLATE'), 'error'),
      });
  }

  cancelForm(): void {
    this.showForm.set(false);
  }
}
