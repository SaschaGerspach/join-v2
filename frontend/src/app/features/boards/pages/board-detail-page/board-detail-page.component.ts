import { Component, inject, signal, computed, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { CdkDragDrop, DragDropModule, moveItemInArray, transferArrayItem } from '@angular/cdk/drag-drop';
import { ColumnsApiService, Column } from '../../../../core/columns/columns-api.service';
import { TasksApiService, Task, CreateTaskPayload } from '../../../../core/tasks/tasks-api.service';
import { BoardsApiService, Board } from '../../../../core/boards/boards-api.service';
import { TaskDetailModalComponent } from '../../components/task-detail-modal/task-detail-modal.component';

@Component({
  selector: 'app-board-detail-page',
  standalone: true,
  imports: [FormsModule, DragDropModule, TaskDetailModalComponent],
  templateUrl: './board-detail-page.component.html',
  styleUrl: './board-detail-page.component.scss',
})
export class BoardDetailPageComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly boardsApi = inject(BoardsApiService);
  private readonly columnsApi = inject(ColumnsApiService);
  private readonly tasksApi = inject(TasksApiService);

  boardId = signal<number>(0);
  board = signal<Board | null>(null);
  columns = signal<Column[]>([]);
  tasks = signal<Task[]>([]);

  columnListIds = computed(() => this.columns().map(c => `col-${c.id}`));

  newColumnTitle = '';
  showColumnForm = signal(false);

  addingTaskForColumn = signal<number | null>(null);
  newTaskTitle = '';

  selectedTask = signal<Task | null>(null);

  ngOnInit(): void {
    const id = Number(this.route.snapshot.paramMap.get('id'));
    this.boardId.set(id);
    this.loadData(id);
  }

  loadData(boardId: number): void {
    this.boardsApi.getById(boardId).subscribe(board => this.board.set(board));
    this.columnsApi.getByBoard(boardId).subscribe(cols => this.columns.set(cols));
    this.tasksApi.getByBoard(boardId).subscribe(tasks => this.tasks.set(tasks));
  }

  tasksForColumn(columnId: number): Task[] {
    return this.tasks().filter(t => t.column === columnId);
  }

  createColumn(): void {
    const title = this.newColumnTitle.trim();
    if (!title) return;

    this.columnsApi.create(this.boardId(), title).subscribe(col => {
      this.columns.update(c => [...c, col]);
      this.newColumnTitle = '';
      this.showColumnForm.set(false);
    });
  }

  deleteColumn(id: number): void {
    this.columnsApi.delete(id).subscribe(() => {
      this.columns.update(c => c.filter(col => col.id !== id));
      this.tasks.update(t => t.filter(task => task.column !== id));
    });
  }

  startAddTask(columnId: number): void {
    this.addingTaskForColumn.set(columnId);
    this.newTaskTitle = '';
  }

  createTask(columnId: number): void {
    const title = this.newTaskTitle.trim();
    if (!title) return;

    const payload: CreateTaskPayload = { title, column: columnId };
    this.tasksApi.create(this.boardId(), payload).subscribe(task => {
      this.tasks.update(t => [...t, task]);
      this.addingTaskForColumn.set(null);
      this.newTaskTitle = '';
    });
  }

  openTask(task: Task): void {
    this.selectedTask.set(task);
  }

  onTaskUpdated(updated: Task): void {
    this.tasks.update(t => t.map(task => task.id === updated.id ? updated : task));
  }

  onTaskDeleted(id: number): void {
    this.tasks.update(t => t.filter(task => task.id !== id));
  }

  deleteTask(id: number): void {
    this.tasksApi.delete(id).subscribe(() => {
      this.tasks.update(t => t.filter(task => task.id !== id));
    });
  }

  drop(event: CdkDragDrop<Task[]>, targetColumnId: number): void {
    const task: Task = event.item.data;

    if (event.previousContainer === event.container) {
      // reorder within same column — no API call needed for now
      return;
    }

    // Optimistic update: change the task's column in local state
    this.tasks.update(tasks =>
      tasks.map(t => t.id === task.id ? { ...t, column: targetColumnId } : t)
    );

    // Persist to backend
    this.tasksApi.patch(task.id, { column: targetColumnId }).subscribe();
  }

  priorityClass(priority: string): string {
    return `priority-${priority}`;
  }
}
