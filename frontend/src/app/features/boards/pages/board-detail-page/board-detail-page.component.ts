import { Component, inject, signal, computed, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { SlicePipe } from '@angular/common';
import { CdkDragDrop, DragDropModule, moveItemInArray, transferArrayItem } from '@angular/cdk/drag-drop';
import { ColumnsApiService, Column } from '../../../../core/columns/columns-api.service';
import { TasksApiService, Task, CreateTaskPayload } from '../../../../core/tasks/tasks-api.service';
import { BoardsApiService, Board } from '../../../../core/boards/boards-api.service';
import { ContactsApiService, Contact } from '../../../../core/contacts/contacts-api.service';
import { TaskDetailModalComponent } from '../../components/task-detail-modal/task-detail-modal.component';
import { LoadingSpinnerComponent } from '../../../../shared/components/loading-spinner/loading-spinner.component';

@Component({
  selector: 'app-board-detail-page',
  standalone: true,
  imports: [FormsModule, DragDropModule, SlicePipe, TaskDetailModalComponent, LoadingSpinnerComponent],
  templateUrl: './board-detail-page.component.html',
  styleUrl: './board-detail-page.component.scss',
})
export class BoardDetailPageComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly boardsApi = inject(BoardsApiService);
  private readonly columnsApi = inject(ColumnsApiService);
  private readonly tasksApi = inject(TasksApiService);
  private readonly contactsApi = inject(ContactsApiService);

  boardId = signal<number>(0);
  board = signal<Board | null>(null);
  columns = signal<Column[]>([]);
  tasks = signal<Task[]>([]);
  contacts = signal<Contact[]>([]);

  columnListIds = computed(() => this.columns().map(c => `col-${c.id}`));

  newColumnTitle = '';
  showColumnForm = signal(false);

  addingTaskForColumn = signal<number | null>(null);
  newTaskTitle = '';

  selectedTask = signal<Task | null>(null);
  loading = signal(true);
  error = signal('');

  ngOnInit(): void {
    const id = Number(this.route.snapshot.paramMap.get('id'));
    this.boardId.set(id);
    this.loadData(id);
  }

  loadData(boardId: number): void {
    this.loading.set(true);
    this.error.set('');
    this.boardsApi.getById(boardId).subscribe({
      next: board => this.board.set(board),
      error: () => { this.error.set('Failed to load board.'); this.loading.set(false); },
    });
    this.columnsApi.getByBoard(boardId).subscribe(cols => this.columns.set(cols));
    this.tasksApi.getByBoard(boardId).subscribe(tasks => {
      this.tasks.set(tasks);
      this.loading.set(false);
    });
    this.contactsApi.getAll().subscribe(contacts => this.contacts.set(contacts));
  }

  contactName(id: number | null): string {
    if (!id) return '';
    const c = this.contacts().find(x => x.id === id);
    return c ? `${c.first_name} ${c.last_name}` : '';
  }

  contactInitials(id: number | null): string {
    if (!id) return '';
    const c = this.contacts().find(x => x.id === id);
    return c ? (c.first_name[0] ?? '') + (c.last_name[0] ?? '') : '';
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
    const isSameColumn = event.previousContainer === event.container;

    if (isSameColumn) {
      const colTasks = this.tasksForColumn(targetColumnId);
      const reordered = [...colTasks];
      const [moved] = reordered.splice(event.previousIndex, 1);
      reordered.splice(event.currentIndex, 0, moved);
      const updated = reordered.map((t, i) => ({ ...t, order: i }));
      this.tasks.update(tasks =>
        tasks.map(t => updated.find(u => u.id === t.id) ?? t)
      );
      this.tasksApi.reorder(updated.map(t => ({ id: t.id, order: t.order, column: t.column }))).subscribe();
    } else {
      const prevTasks = this.tasksForColumn(task.column!).filter(t => t.id !== task.id)
        .map((t, i) => ({ ...t, order: i }));
      const targetTasks = [...this.tasksForColumn(targetColumnId)];
      targetTasks.splice(event.currentIndex, 0, { ...task, column: targetColumnId });
      const updatedTarget = targetTasks.map((t, i) => ({ ...t, order: i, column: targetColumnId }));

      this.tasks.update(tasks =>
        tasks.map(t => {
          const inPrev = prevTasks.find(u => u.id === t.id);
          const inTarget = updatedTarget.find(u => u.id === t.id);
          return inTarget ?? inPrev ?? t;
        })
      );

      this.tasksApi.reorder([
        ...prevTasks.map(t => ({ id: t.id, order: t.order, column: t.column })),
        ...updatedTarget.map(t => ({ id: t.id, order: t.order, column: t.column })),
      ]).subscribe();
    }
  }

  priorityClass(priority: string): string {
    return `priority-${priority}`;
  }
}
