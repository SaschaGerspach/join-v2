import { ChangeDetectionStrategy, Component, OnDestroy, OnInit, inject, signal } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { DragDropModule } from '@angular/cdk/drag-drop';
import { TaskDetailModalComponent } from '../../components/task-detail-modal/task-detail-modal.component';
import { CreateTaskModalComponent } from '../../components/create-task-modal/create-task-modal.component';
import { TaskCardComponent } from '../../components/task-card/task-card.component';
import { BoardFilterBarComponent } from '../../components/board-filter-bar/board-filter-bar.component';
import { BoardMoreMenuComponent } from '../../components/board-more-menu/board-more-menu.component';
import { BoardBulkToolbarComponent } from '../../components/board-bulk-toolbar/board-bulk-toolbar.component';
import { LoadingSpinnerComponent } from '../../../../shared/components/loading-spinner/loading-spinner.component';
import { ConfirmDialogComponent } from '../../../../shared/components/confirm-dialog/confirm-dialog.component';
import { BoardStateService } from '../../services/board-state.service';
import { Column } from '../../../../core/columns/columns-api.service';
import { UserAvatarComponent } from '../../../../shared/components/user-avatar/user-avatar.component';
import { BoardKeyboardNavDirective } from '../../directives/board-keyboard-nav.directive';
import { TranslateModule } from '@ngx-translate/core';

@Component({
  selector: 'app-board-detail-page',
  imports: [
    FormsModule,
    DragDropModule,
    TranslateModule,
    TaskDetailModalComponent,
    CreateTaskModalComponent,
    TaskCardComponent,
    BoardFilterBarComponent,
    BoardMoreMenuComponent,
    BoardBulkToolbarComponent,
    LoadingSpinnerComponent,
    ConfirmDialogComponent,
    UserAvatarComponent,
    BoardKeyboardNavDirective,
  ],
  templateUrl: './board-detail-page.component.html',
  styleUrl: './board-detail-page.component.scss',
  providers: [BoardStateService],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class BoardDetailPageComponent implements OnInit, OnDestroy {
  private readonly route = inject(ActivatedRoute);
  protected readonly state = inject(BoardStateService);

  showColumnForm = signal(false);
  newColumnTitle = signal('');
  editingColumnTitle = signal('');
  boardTitleInput = signal('');

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
}
