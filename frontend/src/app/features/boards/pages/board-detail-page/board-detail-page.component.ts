import { ChangeDetectionStrategy, Component, DestroyRef, OnDestroy, OnInit, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { ActivatedRoute, RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { SlicePipe, UpperCasePipe } from '@angular/common';
import { DragDropModule } from '@angular/cdk/drag-drop';
import { TaskDetailModalComponent } from '../../components/task-detail-modal/task-detail-modal.component';
import { CreateTaskModalComponent } from '../../components/create-task-modal/create-task-modal.component';
import { LoadingSpinnerComponent } from '../../../../shared/components/loading-spinner/loading-spinner.component';
import { ConfirmDialogComponent } from '../../../../shared/components/confirm-dialog/confirm-dialog.component';
import { BoardStateService } from '../../services/board-state.service';
import { BoardsApiService } from '../../../../core/boards/boards-api.service';
import { Column } from '../../../../core/columns/columns-api.service';
import { ToastService } from '../../../../shared/services/toast.service';
import { MarkdownPipe } from '../../../../shared/pipes/markdown.pipe';
import { UserAvatarComponent } from '../../../../shared/components/user-avatar/user-avatar.component';
import { BoardKeyboardNavDirective } from '../../directives/board-keyboard-nav.directive';
import { TranslateModule, TranslateService } from '@ngx-translate/core';

@Component({
  selector: 'app-board-detail-page',
  standalone: true,
  imports: [FormsModule, DragDropModule, SlicePipe, UpperCasePipe, RouterModule, TranslateModule, TaskDetailModalComponent, CreateTaskModalComponent, LoadingSpinnerComponent, ConfirmDialogComponent, MarkdownPipe, UserAvatarComponent, BoardKeyboardNavDirective],
  templateUrl: './board-detail-page.component.html',
  styleUrl: './board-detail-page.component.scss',
  providers: [BoardStateService],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class BoardDetailPageComponent implements OnInit, OnDestroy {
  private readonly route = inject(ActivatedRoute);
  private readonly boardsApi = inject(BoardsApiService);
  private readonly toast = inject(ToastService);
  private readonly translate = inject(TranslateService);
  private readonly destroyRef = inject(DestroyRef);
  protected readonly state = inject(BoardStateService);

  showColumnForm = signal(false);
  newColumnTitle = signal('');
  editingColumnTitle = signal('');
  boardTitleInput = signal('');
  showFilterNameInput = signal(false);
  filterNameInput = signal('');

  ngOnInit(): void {
    this.state.init(Number(this.route.snapshot.paramMap.get('id')));
    const taskId = this.route.snapshot.paramMap.get('taskId');
    if (taskId) {
      this.state.openTaskById(Number(taskId));
    }
  }

  ngOnDestroy(): void {
    this.state.cleanup();
  }

  createColumn(): void {
    this.state.createColumn(this.newColumnTitle());
    this.newColumnTitle.set('');
    this.showColumnForm.set(false);
  }

  startRenameBoardTitle(): void {
    this.boardTitleInput.set(this.state.board()?.title ?? '');
    this.state.editingBoardTitle.set(true);
  }

  confirmRenameBoardTitle(): void {
    this.state.renameBoard(this.boardTitleInput());
  }

  startRenameColumn(col: Column): void {
    this.state.editingColumnId.set(col.id);
    this.editingColumnTitle.set(col.title);
  }

  confirmRenameColumn(id: number): void {
    this.state.renameColumn(id, this.editingColumnTitle());
  }

  onWipLimitChange(columnId: number, event: Event): void {
    const val = (event.target as HTMLInputElement).value;
    this.state.setWipLimit(columnId, val ? parseInt(val, 10) : null);
  }

  inputValue(event: Event): string {
    return (event.target as HTMLInputElement).value;
  }

  shareInviteLink(): void {
    this.boardsApi.createInviteLink(this.state.boardId())
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: res => {
          const url = `${window.location.origin}/boards/join/${res.token}`;
          navigator.clipboard.writeText(url).then(() => {
            this.toast.show(this.translate.instant('INVITE.LINK_COPIED'));
          });
        },
      });
  }

  exportCsv(): void {
    this.boardsApi.exportCsv(this.state.boardId()).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: blob => this.downloadBlob(blob, `board-${this.state.boardId()}.csv`),
    });
  }

  exportPdf(): void {
    this.boardsApi.exportPdf(this.state.boardId()).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: blob => this.downloadBlob(blob, `board-${this.state.boardId()}.pdf`),
    });
  }

  private downloadBlob(blob: Blob, filename: string): void {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  }

  importCsv(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) return;
    this.boardsApi.importCsv(this.state.boardId(), file).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: (res) => {
        this.toast.show(this.translate.instant('BOARD_DETAIL.IMPORT_SUCCESS', { count: res.imported }));
        this.state.reload();
      },
      error: (err) => this.toast.show(err?.error?.detail ?? this.translate.instant('BOARD_DETAIL.IMPORT_FAILED'), 'error'),
    });
    input.value = '';
  }

  saveFilter(): void {
    this.filterNameInput.set('');
    this.showFilterNameInput.set(true);
  }

  confirmSaveFilter(): void {
    const name = this.filterNameInput().trim();
    if (name) {
      this.state.saveCurrentFilter(name);
    }
    this.showFilterNameInput.set(false);
  }

  applySavedFilter(event: Event): void {
    const name = (event.target as HTMLSelectElement).value;
    if (!name) return;
    const filter = this.state.savedFilters().find(f => f.name === name);
    if (filter) this.state.applySavedFilter(filter);
    (event.target as HTMLSelectElement).value = '';
  }
}
