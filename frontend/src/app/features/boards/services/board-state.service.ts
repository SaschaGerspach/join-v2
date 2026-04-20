import { DestroyRef, Injectable, computed, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { forkJoin } from 'rxjs';
import { Title } from '@angular/platform-browser';
import { CdkDragDrop } from '@angular/cdk/drag-drop';
import { AuthService } from '../../../core/auth/auth.service';
import { BoardsApiService, Board } from '../../../core/boards/boards-api.service';
import { ColumnsApiService, Column } from '../../../core/columns/columns-api.service';
import { TasksApiService, Task, CreateTaskPayload } from '../../../core/tasks/tasks-api.service';
import { ContactsApiService, Contact } from '../../../core/contacts/contacts-api.service';
import { ToastService } from '../../../shared/services/toast.service';
import { BoardWsService } from '../../../core/websocket/board-ws.service';
import { connectBoardWebSocket } from './_board-ws-handler';
import { handleColumnDrop, handleTaskDrop } from './_board-drag-drop';
import { bulkMoveTasks, bulkDeleteTasks } from './_board-bulk-ops';

@Injectable()
export class BoardStateService {
  private readonly auth = inject(AuthService);
  private readonly boardsApi = inject(BoardsApiService);
  private readonly columnsApi = inject(ColumnsApiService);
  private readonly tasksApi = inject(TasksApiService);
  private readonly contactsApi = inject(ContactsApiService);
  private readonly toast = inject(ToastService);
  private readonly boardWs = inject(BoardWsService);
  private readonly titleService = inject(Title);
  private readonly destroyRef = inject(DestroyRef);

  readonly boardId = signal<number>(0);
  readonly board = signal<Board | null>(null);
  readonly columns = signal<Column[]>([]);
  readonly tasks = signal<Task[]>([]);
  readonly contacts = signal<Contact[]>([]);
  readonly loading = signal(true);

  readonly searchQuery = signal('');
  readonly filterPriority = signal<string>('');
  readonly filterAssignee = signal<number | ''>('');
  readonly filterDue = signal<'overdue' | 'soon' | ''>('');
  readonly groupBy = signal<'none' | 'priority' | 'assignee'>('none');

  readonly addingTaskForColumn = signal<number | null>(null);
  readonly editingColumnId = signal<number | null>(null);
  readonly editingBoardTitle = signal(false);
  readonly selectedTask = signal<Task | null>(null);

  readonly pendingDeleteColumnId = signal<number | null>(null);
  readonly pendingDeleteTaskId = signal<number | null>(null);

  readonly selectedTaskIds = signal<Set<number>>(new Set());
  readonly bulkMoveTarget = signal<number | null>(null);
  readonly pendingBulkDelete = signal(false);

  readonly columnListIds = computed(() => this.columns().map(c => `col-${c.id}`));
  readonly bulkMode = computed(() => this.selectedTaskIds().size > 0);
  readonly canViewArchive = computed(() => {
    const board = this.board();
    const user = this.auth.user();
    if (!board || !user) return false;
    return board.is_owner || user.is_staff;
  });

  readonly filteredTasks = computed(() => {
    const q = this.searchQuery().trim().toLowerCase();
    const priority = this.filterPriority();
    const assignee = this.filterAssignee();
    const due = this.filterDue();

    return this.tasks().filter(t => {
      if (q && !t.title.toLowerCase().includes(q)) return false;
      if (priority && t.priority !== priority) return false;
      if (assignee !== '' && !t.assigned_to.includes(assignee as number)) return false;
      if (due === 'overdue' && !this.isOverdue(t.due_date)) return false;
      if (due === 'soon' && !(this.isSoon(t.due_date) && !this.isOverdue(t.due_date))) return false;
      return true;
    });
  });

  readonly hasActiveFilter = computed(() =>
    !!this.searchQuery() || !!this.filterPriority() || this.filterAssignee() !== '' || !!this.filterDue()
  );

  private readonly contactMap = computed(() => {
    const map = new Map<number, { name: string; initials: string }>();
    for (const c of this.contacts()) {
      map.set(c.id, {
        name: `${c.first_name} ${c.last_name}`,
        initials: (c.first_name[0] ?? '') + (c.last_name[0] ?? ''),
      });
    }
    return map;
  });

  private readonly tasksByColumn = computed(() => {
    const map = new Map<number, Task[]>();
    for (const t of this.filteredTasks()) {
      if (t.column === null) continue;
      const list = map.get(t.column);
      if (list) list.push(t);
      else map.set(t.column, [t]);
    }
    return map;
  });

  init(boardId: number): void {
    this.boardId.set(boardId);
    this.loadData(boardId);
    connectBoardWebSocket(boardId, this.boardWs, this.tasks, this.columns, this.destroyRef);
  }

  cleanup(): void {
    this.boardWs.disconnect();
  }

  clearFilters(): void {
    this.searchQuery.set('');
    this.filterPriority.set('');
    this.filterAssignee.set('');
    this.filterDue.set('');
  }

  contactName(id: number | null): string {
    if (id === null || id === undefined) return '';
    return this.contactMap().get(id)?.name ?? '';
  }

  contactInitials(id: number | null): string {
    if (id === null || id === undefined) return '';
    return this.contactMap().get(id)?.initials ?? '';
  }

  tasksForColumn(columnId: number): Task[] {
    return this.tasksByColumn().get(columnId) ?? [];
  }

  groupedTasksForColumn(columnId: number): { label: string; tasks: Task[] }[] {
    const tasks = this.tasksForColumn(columnId);
    const mode = this.groupBy();
    if (mode === 'none') return [{ label: '', tasks }];

    const groups = new Map<string, Task[]>();
    const order: string[] = [];

    if (mode === 'priority') {
      for (const p of ['urgent', 'high', 'medium', 'low']) {
        groups.set(p, []);
        order.push(p);
      }
      for (const t of tasks) {
        groups.get(t.priority)!.push(t);
      }
    } else if (mode === 'assignee') {
      groups.set('Unassigned', []);
      order.push('Unassigned');
      for (const t of tasks) {
        if (t.assigned_to.length === 0) {
          groups.get('Unassigned')!.push(t);
        } else {
          for (const id of t.assigned_to) {
            const name = this.contactName(id) || 'Unknown';
            if (!groups.has(name)) {
              groups.set(name, []);
              order.push(name);
            }
            groups.get(name)!.push(t);
          }
        }
      }
    }

    return order
      .filter(label => (groups.get(label)?.length ?? 0) > 0)
      .map(label => ({ label, tasks: groups.get(label)! }));
  }

  createColumn(title: string): void {
    const trimmed = title.trim();
    if (!trimmed) return;
    this.columnsApi.create(this.boardId(), trimmed).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: col => this.columns.update(c => c.some(x => x.id === col.id) ? c : [...c, col]),
      error: () => this.toast.show('Failed to create column.', 'error'),
    });
  }

  renameBoard(title: string): void {
    const trimmed = title.trim();
    if (!trimmed) { this.editingBoardTitle.set(false); return; }
    this.boardsApi.patch(this.boardId(), { title: trimmed }).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: updated => { this.board.set(updated); this.editingBoardTitle.set(false); },
      error: () => this.toast.show('Failed to rename board.', 'error'),
    });
  }

  taskCountForColumn(columnId: number): number {
    return this.tasks().filter(t => t.column === columnId).length;
  }

  isOverWipLimit(column: Column): boolean {
    return column.wip_limit !== null && this.taskCountForColumn(column.id) > column.wip_limit;
  }

  setWipLimit(id: number, value: number | null): void {
    this.columnsApi.patch(id, { wip_limit: value }).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: updated => this.columns.update(cols => cols.map(c => c.id === id ? updated : c)),
      error: () => this.toast.show('Failed to update WIP limit.', 'error'),
    });
  }

  renameColumn(id: number, title: string): void {
    const trimmed = title.trim();
    if (!trimmed) { this.editingColumnId.set(null); return; }
    this.columnsApi.patch(id, { title: trimmed }).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: updated => { this.columns.update(cols => cols.map(c => c.id === id ? updated : c)); this.editingColumnId.set(null); },
      error: () => this.toast.show('Failed to rename column.', 'error'),
    });
  }

  confirmDeleteColumn(): void {
    const id = this.pendingDeleteColumnId();
    if (id === null) return;
    this.columnsApi.delete(id).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: () => {
        this.columns.update(c => c.filter(col => col.id !== id));
        this.tasks.update(t => t.filter(task => task.column !== id));
        this.pendingDeleteColumnId.set(null);
        this.toast.show('Column deleted');
      },
      error: () => this.toast.show('Failed to delete column.', 'error'),
    });
  }

  createTask(payload: CreateTaskPayload): void {
    this.tasksApi.create(this.boardId(), payload).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: task => {
        this.tasks.update(t => t.some(x => x.id === task.id) ? t : [...t, task]);
        this.addingTaskForColumn.set(null);
        this.toast.show('Task created');
      },
      error: () => this.toast.show('Failed to create task.', 'error'),
    });
  }

  onTaskUpdated(updated: Task): void {
    this.tasks.update(t => t.map(task => task.id === updated.id ? updated : task));
  }

  onTaskDeleted(id: number): void {
    this.tasks.update(t => t.filter(task => task.id !== id));
  }

  confirmDeleteTask(): void {
    const id = this.pendingDeleteTaskId();
    if (id === null) return;
    this.tasksApi.delete(id).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: () => {
        this.tasks.update(t => t.filter(task => task.id !== id));
        this.pendingDeleteTaskId.set(null);
        this.toast.show('Task deleted');
      },
      error: () => this.toast.show('Failed to delete task.', 'error'),
    });
  }

  dropColumn(event: CdkDragDrop<Column[]>): void {
    handleColumnDrop(this.columns, this.columnsApi, this.toast, this.destroyRef, event);
  }

  drop(event: CdkDragDrop<Task[]>, targetColumnId: number): void {
    handleTaskDrop(this.tasks, col => this.tasksForColumn(col), this.tasksApi, this.toast, this.destroyRef, event, targetColumnId);
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
    bulkMoveTasks(this.selectedTaskIds, this.bulkMoveTarget, this.tasks, this.tasksApi, this.toast, this.destroyRef);
  }

  confirmBulkDelete(): void {
    bulkDeleteTasks(this.selectedTaskIds, this.pendingBulkDelete, this.tasks, this.tasksApi, this.toast, this.destroyRef);
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

  private loadData(boardId: number): void {
    this.loading.set(true);
    forkJoin({
      board: this.boardsApi.getById(boardId),
      columns: this.columnsApi.getByBoard(boardId),
      tasks: this.tasksApi.getByBoard(boardId),
      contacts: this.contactsApi.getAll(),
    }).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: ({ board, columns, tasks, contacts }) => {
        this.board.set(board);
        this.titleService.setTitle(`${board.title} | Join`);
        this.columns.set(columns);
        this.tasks.set(tasks);
        this.contacts.set(contacts);
        this.loading.set(false);
      },
      error: () => { this.toast.show('Failed to load board.', 'error'); this.loading.set(false); },
    });
  }
}
