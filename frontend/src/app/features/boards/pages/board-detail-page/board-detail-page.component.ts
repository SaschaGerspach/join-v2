import { Component, OnDestroy, OnInit, inject, signal } from '@angular/core';
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
import { Task } from '../../../../core/tasks/tasks-api.service';

@Component({
  selector: 'app-board-detail-page',
  standalone: true,
  imports: [FormsModule, DragDropModule, SlicePipe, RouterModule, TaskDetailModalComponent, CreateTaskModalComponent, LoadingSpinnerComponent, ConfirmDialogComponent],
  templateUrl: './board-detail-page.component.html',
  styleUrl: './board-detail-page.component.scss',
  providers: [BoardStateService],
})
export class BoardDetailPageComponent implements OnInit, OnDestroy {
  private readonly route = inject(ActivatedRoute);
  protected readonly state = inject(BoardStateService);

  readonly boardId = this.state.boardId;
  readonly board = this.state.board;
  readonly columns = this.state.columns;
  readonly tasks = this.state.tasks;
  readonly contacts = this.state.contacts;
  readonly loading = this.state.loading;

  readonly searchQuery = this.state.searchQuery;
  readonly filterPriority = this.state.filterPriority;
  readonly filterAssignee = this.state.filterAssignee;
  readonly filterDue = this.state.filterDue;
  readonly hasActiveFilter = this.state.hasActiveFilter;

  readonly addingTaskForColumn = this.state.addingTaskForColumn;
  readonly editingColumnId = this.state.editingColumnId;
  readonly editingBoardTitle = this.state.editingBoardTitle;
  readonly selectedTask = this.state.selectedTask;

  readonly pendingDeleteColumnId = this.state.pendingDeleteColumnId;
  readonly pendingDeleteTaskId = this.state.pendingDeleteTaskId;

  readonly selectedTaskIds = this.state.selectedTaskIds;
  readonly bulkMoveTarget = this.state.bulkMoveTarget;
  readonly pendingBulkDelete = this.state.pendingBulkDelete;
  readonly bulkMode = this.state.bulkMode;
  readonly columnListIds = this.state.columnListIds;

  showColumnForm = signal(false);
  newColumnTitle = '';
  editingColumnTitle = '';
  boardTitleInput = '';

  ngOnInit(): void {
    const id = Number(this.route.snapshot.paramMap.get('id'));
    this.state.init(id);
  }

  ngOnDestroy(): void {
    this.state.cleanup();
  }

  clearFilters(): void { this.state.clearFilters(); }

  contactName(id: number | null): string { return this.state.contactName(id); }
  contactInitials(id: number | null): string { return this.state.contactInitials(id); }
  tasksForColumn(columnId: number): Task[] { return this.state.tasksForColumn(columnId); }
  priorityClass(priority: string): string { return this.state.priorityClass(priority); }
  isOverdue(dueDate: string | null): boolean { return this.state.isOverdue(dueDate); }
  isSoon(dueDate: string | null): boolean { return this.state.isSoon(dueDate); }

  createColumn(): void {
    this.state.createColumn(this.newColumnTitle);
    this.newColumnTitle = '';
    this.showColumnForm.set(false);
  }

  startRenameBoardTitle(): void {
    this.boardTitleInput = this.state.board()?.title ?? '';
    this.editingBoardTitle.set(true);
  }

  confirmRenameBoardTitle(): void {
    this.state.renameBoard(this.boardTitleInput);
  }

  startRenameColumn(col: Column): void {
    this.editingColumnId.set(col.id);
    this.editingColumnTitle = col.title;
  }

  confirmRenameColumn(id: number): void {
    this.state.renameColumn(id, this.editingColumnTitle);
  }

  deleteColumn(id: number): void { this.pendingDeleteColumnId.set(id); }
  confirmDeleteColumn(): void { this.state.confirmDeleteColumn(); }

  startAddTask(columnId: number): void { this.addingTaskForColumn.set(columnId); }
  createTask(payload: Parameters<BoardStateService['createTask']>[0]): void { this.state.createTask(payload); }
  openTask(task: Task): void { this.selectedTask.set(task); }
  onTaskUpdated(updated: Task): void { this.state.onTaskUpdated(updated); }
  onTaskDeleted(id: number): void { this.state.onTaskDeleted(id); }

  deleteTask(id: number): void { this.pendingDeleteTaskId.set(id); }
  confirmDeleteTask(): void { this.state.confirmDeleteTask(); }

  dropColumn(event: Parameters<BoardStateService['dropColumn']>[0]): void { this.state.dropColumn(event); }
  drop(event: Parameters<BoardStateService['drop']>[0], targetColumnId: number): void { this.state.drop(event, targetColumnId); }

  toggleTaskSelection(taskId: number, event: Event): void { this.state.toggleTaskSelection(taskId, event); }
  isTaskSelected(taskId: number): boolean { return this.state.isTaskSelected(taskId); }
  clearSelection(): void { this.state.clearSelection(); }

  bulkMove(): void { this.state.bulkMove(); }
  bulkDelete(): void { this.pendingBulkDelete.set(true); }
  confirmBulkDelete(): void { this.state.confirmBulkDelete(); }
}
