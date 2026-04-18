import { ChangeDetectionStrategy, Component, OnDestroy, OnInit, inject, signal } from '@angular/core';
import { ActivatedRoute, RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { SlicePipe } from '@angular/common';
import { DragDropModule } from '@angular/cdk/drag-drop';
import { TaskDetailModalComponent } from '../../components/task-detail-modal/task-detail-modal.component';
import { CreateTaskModalComponent } from '../../components/create-task-modal/create-task-modal.component';
import { LoadingSpinnerComponent } from '../../../../shared/components/loading-spinner/loading-spinner.component';
import { ConfirmDialogComponent } from '../../../../shared/components/confirm-dialog/confirm-dialog.component';
import { BoardStateService } from '../../services/board-state.service';
import { Column } from '../../../../core/columns/columns-api.service';

@Component({
  selector: 'app-board-detail-page',
  standalone: true,
  imports: [FormsModule, DragDropModule, SlicePipe, RouterModule, TaskDetailModalComponent, CreateTaskModalComponent, LoadingSpinnerComponent, ConfirmDialogComponent],
  templateUrl: './board-detail-page.component.html',
  styleUrl: './board-detail-page.component.scss',
  providers: [BoardStateService],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class BoardDetailPageComponent implements OnInit, OnDestroy {
  private readonly route = inject(ActivatedRoute);
  protected readonly state = inject(BoardStateService);

  showColumnForm = signal(false);
  newColumnTitle = '';
  editingColumnTitle = '';
  boardTitleInput = '';

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

  inputValue(event: Event): string {
    return (event.target as HTMLInputElement).value;
  }
}
