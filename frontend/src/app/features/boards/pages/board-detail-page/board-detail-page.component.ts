import { ChangeDetectionStrategy, Component, ElementRef, HostListener, OnDestroy, OnInit, ViewChild, inject, signal } from '@angular/core';
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
import { TranslateModule, TranslateService } from '@ngx-translate/core';

@Component({
  selector: 'app-board-detail-page',
  standalone: true,
  imports: [FormsModule, DragDropModule, SlicePipe, UpperCasePipe, RouterModule, TranslateModule, TaskDetailModalComponent, CreateTaskModalComponent, LoadingSpinnerComponent, ConfirmDialogComponent, MarkdownPipe, UserAvatarComponent],
  templateUrl: './board-detail-page.component.html',
  styleUrl: './board-detail-page.component.scss',
  providers: [BoardStateService],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class BoardDetailPageComponent implements OnInit, OnDestroy {
  @ViewChild('searchInput') searchInput!: ElementRef<HTMLInputElement>;
  private readonly route = inject(ActivatedRoute);
  private readonly boardsApi = inject(BoardsApiService);
  private readonly toast = inject(ToastService);
  private readonly translate = inject(TranslateService);
  protected readonly state = inject(BoardStateService);

  showColumnForm = signal(false);
  newColumnTitle = '';
  editingColumnTitle = '';
  boardTitleInput = '';

  focusedColumnIndex = signal(-1);
  focusedTaskIndex = signal(-1);

  focusedColumnId(): number | null {
    const cols = this.state.columns();
    const idx = this.focusedColumnIndex();
    return idx >= 0 && idx < cols.length ? cols[idx].id : null;
  }

  focusedTaskId(): number | null {
    const colId = this.focusedColumnId();
    if (colId === null) return null;
    const tasks = this.state.tasksForColumn(colId);
    const idx = this.focusedTaskIndex();
    return idx >= 0 && idx < tasks.length ? tasks[idx].id : null;
  }

  ngOnInit(): void {
    this.state.init(Number(this.route.snapshot.paramMap.get('id')));
  }

  ngOnDestroy(): void {
    this.state.cleanup();
  }

  createColumn(): void {
    this.state.createColumn(this.newColumnTitle);
    this.newColumnTitle = '';
    this.showColumnForm.set(false);
  }

  startRenameBoardTitle(): void {
    this.boardTitleInput = this.state.board()?.title ?? '';
    this.state.editingBoardTitle.set(true);
  }

  confirmRenameBoardTitle(): void {
    this.state.renameBoard(this.boardTitleInput);
  }

  startRenameColumn(col: Column): void {
    this.state.editingColumnId.set(col.id);
    this.editingColumnTitle = col.title;
  }

  confirmRenameColumn(id: number): void {
    this.state.renameColumn(id, this.editingColumnTitle);
  }

  onWipLimitChange(columnId: number, event: Event): void {
    const val = (event.target as HTMLInputElement).value;
    this.state.setWipLimit(columnId, val ? parseInt(val, 10) : null);
  }

  inputValue(event: Event): string {
    return (event.target as HTMLInputElement).value;
  }

  exportCsv(): void {
    this.boardsApi.exportCsv(this.state.boardId()).subscribe({
      next: blob => {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `board-${this.state.boardId()}.csv`;
        a.click();
        URL.revokeObjectURL(url);
      },
      error: () => this.toast.show('Export failed.', 'error'),
    });
  }

  importCsv(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) return;
    this.boardsApi.importCsv(this.state.boardId(), file).subscribe({
      next: (res) => {
        this.toast.show(this.translate.instant('BOARD_DETAIL.IMPORT_SUCCESS', { count: res.imported }));
        this.state.reload();
      },
      error: (err) => this.toast.show(err?.error?.detail ?? this.translate.instant('BOARD_DETAIL.IMPORT_FAILED'), 'error'),
    });
    input.value = '';
  }

  saveFilter(): void {
    const name = prompt(this.translate.instant('BOARD_DETAIL.FILTER_NAME'));
    if (name?.trim()) {
      this.state.saveCurrentFilter(name.trim());
    }
  }

  applySavedFilter(event: Event): void {
    const name = (event.target as HTMLSelectElement).value;
    if (!name) return;
    const filter = this.state.savedFilters().find(f => f.name === name);
    if (filter) this.state.applySavedFilter(filter);
    (event.target as HTMLSelectElement).value = '';
  }

  @HostListener('document:keydown', ['$event'])
  onKeydown(event: KeyboardEvent): void {
    if (event.target instanceof HTMLInputElement || event.target instanceof HTMLTextAreaElement || event.target instanceof HTMLSelectElement) return;
    if (this.state.selectedTask() || this.state.addingTaskForColumn() !== null) return;

    const columns = this.state.columns();
    if (!columns.length) return;

    switch (event.key) {
      case '/':
        event.preventDefault();
        this.searchInput?.nativeElement?.focus();
        break;
      case 'n': {
        const colIdx = Math.max(0, this.focusedColumnIndex());
        this.state.addingTaskForColumn.set(columns[colIdx].id);
        break;
      }
      case 'ArrowRight': {
        event.preventDefault();
        const next = Math.min(this.focusedColumnIndex() + 1, columns.length - 1);
        this.focusedColumnIndex.set(next);
        this.focusedTaskIndex.set(0);
        break;
      }
      case 'ArrowLeft': {
        event.preventDefault();
        const prev = Math.max(this.focusedColumnIndex() - 1, 0);
        this.focusedColumnIndex.set(prev);
        this.focusedTaskIndex.set(0);
        break;
      }
      case 'ArrowDown': {
        event.preventDefault();
        const colIdx = Math.max(0, this.focusedColumnIndex());
        const tasks = this.state.tasksForColumn(columns[colIdx].id);
        this.focusedTaskIndex.set(Math.min(this.focusedTaskIndex() + 1, tasks.length - 1));
        break;
      }
      case 'ArrowUp': {
        event.preventDefault();
        this.focusedTaskIndex.set(Math.max(this.focusedTaskIndex() - 1, 0));
        break;
      }
      case 'Enter': {
        const colIdx = this.focusedColumnIndex();
        const taskIdx = this.focusedTaskIndex();
        if (colIdx >= 0 && taskIdx >= 0) {
          const tasks = this.state.tasksForColumn(columns[colIdx].id);
          if (tasks[taskIdx]) {
            this.state.selectedTask.set(tasks[taskIdx]);
          }
        }
        break;
      }
      case 'Escape':
        this.focusedColumnIndex.set(-1);
        this.focusedTaskIndex.set(-1);
        break;
    }
  }
}
