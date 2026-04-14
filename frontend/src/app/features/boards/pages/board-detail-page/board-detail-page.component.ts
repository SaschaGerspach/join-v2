import { Component, inject, signal, computed, OnInit, OnDestroy } from '@angular/core';
import { Subscription } from 'rxjs';
import { ActivatedRoute, RouterModule } from '@angular/router';
import { Title } from '@angular/platform-browser';
import { FormsModule } from '@angular/forms';
import { SlicePipe } from '@angular/common';
import { CdkDragDrop, DragDropModule } from '@angular/cdk/drag-drop';
import { ColumnsApiService, Column } from '../../../../core/columns/columns-api.service';
import { TasksApiService, Task, CreateTaskPayload } from '../../../../core/tasks/tasks-api.service';
import { BoardsApiService, Board } from '../../../../core/boards/boards-api.service';
import { ContactsApiService, Contact } from '../../../../core/contacts/contacts-api.service';
import { TaskDetailModalComponent } from '../../components/task-detail-modal/task-detail-modal.component';
import { CreateTaskModalComponent } from '../../components/create-task-modal/create-task-modal.component';
import { LoadingSpinnerComponent } from '../../../../shared/components/loading-spinner/loading-spinner.component';
import { ConfirmDialogComponent } from '../../../../shared/components/confirm-dialog/confirm-dialog.component';
import { ToastService } from '../../../../shared/services/toast.service';
import { BoardWsService } from '../../../../core/websocket/board-ws.service';

@Component({
  selector: 'app-board-detail-page',
  standalone: true,
  imports: [FormsModule, DragDropModule, SlicePipe, RouterModule, TaskDetailModalComponent, CreateTaskModalComponent, LoadingSpinnerComponent, ConfirmDialogComponent],
  templateUrl: './board-detail-page.component.html',
  styleUrl: './board-detail-page.component.scss',
})
export class BoardDetailPageComponent implements OnInit, OnDestroy {
  private readonly route = inject(ActivatedRoute);
  private readonly titleService = inject(Title);
  private readonly boardsApi = inject(BoardsApiService);
  private readonly columnsApi = inject(ColumnsApiService);
  private readonly tasksApi = inject(TasksApiService);
  private readonly contactsApi = inject(ContactsApiService);
  private readonly toast = inject(ToastService);
  private readonly boardWs = inject(BoardWsService);
  private wsSub?: Subscription;

  boardId = signal<number>(0);
  board = signal<Board | null>(null);
  columns = signal<Column[]>([]);
  tasks = signal<Task[]>([]);
  contacts = signal<Contact[]>([]);

  columnListIds = computed(() => this.columns().map(c => `col-${c.id}`));

  searchQuery = signal('');
  filterPriority = signal<string>('');
  filterAssignee = signal<number | ''>('');
  filterDue = signal<'overdue' | 'soon' | ''>('');

  filteredTasks = computed(() => {
    const q = this.searchQuery().trim().toLowerCase();
    const priority = this.filterPriority();
    const assignee = this.filterAssignee();
    const due = this.filterDue();

    return this.tasks().filter(t => {
      if (q && !t.title.toLowerCase().includes(q)) return false;
      if (priority && t.priority !== priority) return false;
      if (assignee !== '' && t.assigned_to !== assignee) return false;
      if (due === 'overdue' && !this.isOverdue(t.due_date)) return false;
      if (due === 'soon' && !(this.isSoon(t.due_date) && !this.isOverdue(t.due_date))) return false;
      return true;
    });
  });

  hasActiveFilter = computed(() =>
    !!this.searchQuery() || !!this.filterPriority() || this.filterAssignee() !== '' || !!this.filterDue()
  );

  clearFilters(): void {
    this.searchQuery.set('');
    this.filterPriority.set('');
    this.filterAssignee.set('');
    this.filterDue.set('');
  }

  newColumnTitle = '';
  showColumnForm = signal(false);

  addingTaskForColumn = signal<number | null>(null);

  editingColumnId = signal<number | null>(null);
  editingColumnTitle = '';

  editingBoardTitle = signal(false);
  boardTitleInput = '';

  selectedTask = signal<Task | null>(null);
  loading = signal(true);

  pendingDeleteColumnId = signal<number | null>(null);
  pendingDeleteTaskId = signal<number | null>(null);

  selectedTaskIds = signal<Set<number>>(new Set());
  bulkMode = computed(() => this.selectedTaskIds().size > 0);
  bulkMoveTarget = signal<number | null>(null);
  pendingBulkDelete = signal(false);

  ngOnInit(): void {
    const id = Number(this.route.snapshot.paramMap.get('id'));
    this.boardId.set(id);
    this.loadData(id);
    this.connectWebSocket(id);
  }

  ngOnDestroy(): void {
    this.wsSub?.unsubscribe();
    this.boardWs.disconnect();
  }

  private connectWebSocket(boardId: number): void {
    this.boardWs.connect(boardId);
    this.wsSub = this.boardWs.events$.subscribe(evt => {
      switch (evt.event) {
        case 'task_created':
          this.tasks.update(t => t.some(x => x.id === evt.data.id) ? t : [...t, evt.data]);
          break;
        case 'task_updated':
          this.tasks.update(t => t.map(x => x.id === evt.data.id ? evt.data : x));
          break;
        case 'task_deleted':
          this.tasks.update(t => t.filter(x => x.id !== evt.data.id));
          break;
        case 'tasks_reordered':
          this.tasks.update(tasks => {
            const updated = evt.data as any[];
            return tasks.map(t => {
              const u = updated.find((x: any) => x.id === t.id);
              return u ?? t;
            });
          });
          break;
        case 'column_created':
          this.columns.update(c => c.some(x => x.id === evt.data.id) ? c : [...c, evt.data]);
          break;
        case 'column_updated':
          this.columns.update(c => c.map(x => x.id === evt.data.id ? evt.data : x));
          break;
        case 'column_deleted':
          this.columns.update(c => c.filter(x => x.id !== evt.data.id));
          break;
      }
    });
  }

  loadData(boardId: number): void {
    this.loading.set(true);
    this.boardsApi.getById(boardId).subscribe({
      next: board => {
        this.board.set(board);
        this.titleService.setTitle(`${board.title} | Join`);
      },
      error: () => { this.toast.show('Failed to load board.', 'error'); this.loading.set(false); },
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
    return this.filteredTasks().filter(t => t.column === columnId);
  }

  createColumn(): void {
    const title = this.newColumnTitle.trim();
    if (!title) return;

    this.columnsApi.create(this.boardId(), title).subscribe({
      next: col => {
        this.columns.update(c => c.some(x => x.id === col.id) ? c : [...c, col]);
        this.newColumnTitle = '';
        this.showColumnForm.set(false);
      },
      error: () => this.toast.show('Failed to create column.', 'error'),
    });
  }

  startRenameBoardTitle(): void {
    this.boardTitleInput = this.board()?.title ?? '';
    this.editingBoardTitle.set(true);
  }

  confirmRenameBoardTitle(): void {
    const title = this.boardTitleInput.trim();
    if (!title) { this.editingBoardTitle.set(false); return; }
    this.boardsApi.patch(this.boardId(), { title }).subscribe({
      next: updated => {
        this.board.set(updated);
        this.editingBoardTitle.set(false);
      },
      error: () => this.toast.show('Failed to rename board.', 'error'),
    });
  }

  startRenameColumn(col: Column): void {
    this.editingColumnId.set(col.id);
    this.editingColumnTitle = col.title;
  }

  confirmRenameColumn(id: number): void {
    const title = this.editingColumnTitle.trim();
    if (!title) { this.editingColumnId.set(null); return; }
    this.columnsApi.patch(id, { title }).subscribe({
      next: updated => {
        this.columns.update(cols => cols.map(c => c.id === id ? updated : c));
        this.editingColumnId.set(null);
      },
      error: () => this.toast.show('Failed to rename column.', 'error'),
    });
  }

  deleteColumn(id: number): void {
    this.pendingDeleteColumnId.set(id);
  }

  confirmDeleteColumn(): void {
    const id = this.pendingDeleteColumnId();
    if (id === null) return;
    this.columnsApi.delete(id).subscribe({
      next: () => {
        this.columns.update(c => c.filter(col => col.id !== id));
        this.tasks.update(t => t.filter(task => task.column !== id));
        this.pendingDeleteColumnId.set(null);
        this.toast.show('Column deleted');
      },
      error: () => this.toast.show('Failed to delete column.', 'error'),
    });
  }

  startAddTask(columnId: number): void {
    this.addingTaskForColumn.set(columnId);
  }

  createTask(payload: CreateTaskPayload): void {
    this.tasksApi.create(this.boardId(), payload).subscribe({
      next: task => {
        this.tasks.update(t => t.some(x => x.id === task.id) ? t : [...t, task]);
        this.addingTaskForColumn.set(null);
        this.toast.show('Task created');
      },
      error: () => this.toast.show('Failed to create task.', 'error'),
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
    this.pendingDeleteTaskId.set(id);
  }

  confirmDeleteTask(): void {
    const id = this.pendingDeleteTaskId();
    if (id === null) return;
    this.tasksApi.delete(id).subscribe({
      next: () => {
        this.tasks.update(t => t.filter(task => task.id !== id));
        this.pendingDeleteTaskId.set(null);
        this.toast.show('Task deleted');
      },
      error: () => this.toast.show('Failed to delete task.', 'error'),
    });
  }

  dropColumn(event: CdkDragDrop<Column[]>): void {
    if (event.previousIndex === event.currentIndex) return;
    const snapshot = this.columns();
    const reordered = [...snapshot];
    const [moved] = reordered.splice(event.previousIndex, 1);
    reordered.splice(event.currentIndex, 0, moved);
    const updated = reordered.map((c, i) => ({ ...c, order: i }));
    this.columns.set(updated);

    let failed = false;
    updated.forEach(col => this.columnsApi.patch(col.id, { order: col.order }).subscribe({
      error: () => {
        if (failed) return;
        failed = true;
        this.columns.set(snapshot);
        this.toast.show('Failed to reorder columns.', 'error');
      },
    }));
  }

  drop(event: CdkDragDrop<Task[]>, targetColumnId: number): void {
    const task: Task = event.item.data;
    const isSameColumn = event.previousContainer === event.container;
    const snapshot = this.tasks();

    if (isSameColumn) {
      const colTasks = this.tasksForColumn(targetColumnId);
      const reordered = [...colTasks];
      const [moved] = reordered.splice(event.previousIndex, 1);
      reordered.splice(event.currentIndex, 0, moved);
      const updated = reordered.map((t, i) => ({ ...t, order: i }));
      this.tasks.update(tasks =>
        tasks.map(t => updated.find(u => u.id === t.id) ?? t)
      );
      this.tasksApi.reorder(updated.map(t => ({ id: t.id, order: t.order, column: t.column }))).subscribe({
        error: () => {
          this.tasks.set(snapshot);
          this.toast.show('Failed to reorder tasks.', 'error');
        },
      });
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
      ]).subscribe({
        error: () => {
          this.tasks.set(snapshot);
          this.toast.show('Failed to move task.', 'error');
        },
      });
    }
  }

  toggleTaskSelection(taskId: number, event: Event): void {
    event.stopPropagation();
    this.selectedTaskIds.update(set => {
      const next = new Set(set);
      if (next.has(taskId)) next.delete(taskId);
      else next.add(taskId);
      return next;
    });
  }

  isTaskSelected(taskId: number): boolean {
    return this.selectedTaskIds().has(taskId);
  }

  clearSelection(): void {
    this.selectedTaskIds.set(new Set());
  }

  bulkMove(): void {
    const targetCol = this.bulkMoveTarget();
    if (targetCol === null) return;
    const ids = [...this.selectedTaskIds()];
    const items = ids.map((id, i) => ({ id, order: i, column: targetCol }));
    const snapshot = this.tasks();

    this.tasks.update(tasks =>
      tasks.map(t => ids.includes(t.id) ? { ...t, column: targetCol } : t)
    );
    this.clearSelection();

    this.tasksApi.reorder(items).subscribe({
      next: () => this.toast.show(`Moved ${ids.length} task(s)`),
      error: () => {
        this.tasks.set(snapshot);
        this.toast.show('Failed to move tasks.', 'error');
      },
    });
  }

  bulkDelete(): void {
    this.pendingBulkDelete.set(true);
  }

  confirmBulkDelete(): void {
    const ids = [...this.selectedTaskIds()];
    this.pendingBulkDelete.set(false);
    let done = 0;
    ids.forEach(id => {
      this.tasksApi.delete(id).subscribe({
        next: () => {
          this.tasks.update(t => t.filter(task => task.id !== id));
          done++;
          if (done === ids.length) {
            this.clearSelection();
            this.toast.show(`Deleted ${ids.length} task(s)`);
          }
        },
        error: () => this.toast.show('Failed to delete some tasks.', 'error'),
      });
    });
  }

  priorityClass(priority: string): string {
    return `priority-${priority}`;
  }

  isOverdue(dueDate: string | null): boolean {
    if (!dueDate) return false;
    return new Date(dueDate) < new Date(new Date().toDateString());
  }

  isSoon(dueDate: string | null): boolean {
    if (!dueDate) return false;
    const today = new Date(new Date().toDateString());
    const due = new Date(dueDate);
    const diff = (due.getTime() - today.getTime()) / (1000 * 60 * 60 * 24);
    return diff >= 0 && diff <= 3;
  }
}
