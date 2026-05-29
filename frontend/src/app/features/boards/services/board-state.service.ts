import { DestroyRef, Injectable, computed, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { ActivatedRoute, Router } from '@angular/router';
import { forkJoin } from 'rxjs';
import { Title } from '@angular/platform-browser';
import { CdkDragDrop } from '@angular/cdk/drag-drop';
import { TranslateService } from '@ngx-translate/core';
import { AuthService } from '../../../core/auth/auth.service';
import { BoardsApiService, Board } from '../../../core/boards/boards-api.service';
import { ColumnsApiService, Column } from '../../../core/columns/columns-api.service';
import { TasksApiService, Task, CreateTaskPayload } from '../../../core/tasks/tasks-api.service';
import { ContactsApiService, Contact } from '../../../core/contacts/contacts-api.service';
import { ToastService } from '../../../shared/services/toast.service';
import { BoardWsService, PresenceUser } from '../../../core/websocket/board-ws.service';
import { connectBoardWebSocket } from './_board-ws-handler';
import { handleColumnDrop, handleTaskDrop } from './_board-drag-drop';
import { bulkMoveTasks, bulkDeleteTasks } from './_board-bulk-ops';
import {
  SavedFilter,
  restoreFiltersFromUrl,
  createFilterUrlSync,
  filterTasks,
  loadSavedFilters,
  persistSavedFilters,
  isOverdue,
  isSoon,
} from './_board-filters';
import { groupTasksByMode } from './_board-grouping';

export { SavedFilter } from './_board-filters';

@Injectable()
export class BoardStateService {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);
  private readonly boardsApi = inject(BoardsApiService);
  private readonly columnsApi = inject(ColumnsApiService);
  private readonly tasksApi = inject(TasksApiService);
  private readonly contactsApi = inject(ContactsApiService);
  private readonly toast = inject(ToastService);
  private readonly translate = inject(TranslateService);
  private readonly boardWs = inject(BoardWsService);
  private readonly titleService = inject(Title);
  private readonly destroyRef = inject(DestroyRef);

  readonly boardId = signal<number>(0);
  readonly board = signal<Board | null>(null);
  readonly columns = signal<Column[]>([]);
  readonly tasks = signal<Task[]>([]);
  readonly contacts = signal<Contact[]>([]);
  readonly onlineUsers = signal<PresenceUser[]>([]);
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
  readonly savedFilters = signal<SavedFilter[]>([]);
  readonly columnTaskLimits = signal<Map<number, number>>(new Map());
  private readonly COLUMN_TASK_LIMIT = 50;
  private readonly COLUMN_TASK_INCREMENT = 50;

  readonly columnListIds = computed(() => this.columns().map(c => `col-${c.id}`));
  readonly bulkMode = computed(() => this.selectedTaskIds().size > 0);
  readonly canViewArchive = computed(() => {
    const board = this.board();
    const user = this.auth.user();
    if (!board || !user) return false;
    return board.is_owner || user.is_staff;
  });

  readonly filteredTasks = computed(() =>
    filterTasks(this.tasks(), this.searchQuery(), this.filterPriority(), this.filterAssignee(), this.filterDue())
  );

  readonly hasActiveFilter = computed(() =>
    !!this.searchQuery() || !!this.filterPriority() || this.filterAssignee() !== '' || !!this.filterDue()
  );

  readonly dragDisabled = computed(() => this.hasActiveFilter() || this.groupBy() !== 'none');

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

  private readonly taskCountByColumn = computed(() => {
    const counts = new Map<number, number>();
    for (const t of this.tasks()) {
      if (t.column != null) {
        counts.set(t.column, (counts.get(t.column) ?? 0) + 1);
      }
    }
    return counts;
  });

  private pendingTaskId: number | null = null;
  private skipUrlSync = { value: false };

  constructor() {
    createFilterUrlSync(
      this.router, this.route,
      this.searchQuery, this.filterPriority, this.filterAssignee, this.filterDue, this.groupBy,
      this.skipUrlSync, this.destroyRef,
    );
  }

  init(boardId: number): void {
    this.boardId.set(boardId);
    restoreFiltersFromUrl(this.route, this.searchQuery, this.filterPriority, this.filterAssignee, this.filterDue, this.groupBy, this.skipUrlSync);
    this.loadData(boardId);
    this.savedFilters.set(loadSavedFilters(boardId));
    connectBoardWebSocket(boardId, this.boardWs, this.tasks, this.columns, this.onlineUsers, this.destroyRef);
  }

  openTaskById(taskId: number): void {
    this.pendingTaskId = taskId;
  }

  cleanup(): void {
    this.boardWs.disconnect();
  }

  reload(): void {
    this.loadData(this.boardId());
  }

  clearFilters(): void {
    this.searchQuery.set('');
    this.filterPriority.set('');
    this.filterAssignee.set('');
    this.filterDue.set('');
  }

  saveCurrentFilter(name: string): void {
    const filter: SavedFilter = {
      name,
      priority: this.filterPriority(),
      assignee: this.filterAssignee(),
      due: this.filterDue(),
      search: this.searchQuery(),
    };
    const filters = [...this.savedFilters(), filter];
    this.savedFilters.set(filters);
    persistSavedFilters(this.boardId(), filters);
  }

  applySavedFilter(filter: SavedFilter): void {
    this.searchQuery.set(filter.search);
    this.filterPriority.set(filter.priority);
    this.filterAssignee.set(filter.assignee);
    this.filterDue.set(filter.due);
  }

  deleteSavedFilter(name: string): void {
    const filters = this.savedFilters().filter(f => f.name !== name);
    this.savedFilters.set(filters);
    persistSavedFilters(this.boardId(), filters);
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
    const all = this.tasksByColumn().get(columnId) ?? [];
    const limit = this.columnTaskLimits().get(columnId) ?? this.COLUMN_TASK_LIMIT;
    if (limit >= all.length) return all;
    return all.slice(0, limit);
  }

  allTasksForColumn(columnId: number): Task[] {
    return this.tasksByColumn().get(columnId) ?? [];
  }

  hasMoreTasks(columnId: number): boolean {
    const total = this.tasksByColumn().get(columnId)?.length ?? 0;
    const limit = this.columnTaskLimits().get(columnId) ?? this.COLUMN_TASK_LIMIT;
    return total > limit;
  }

  hiddenTaskCount(columnId: number): number {
    const total = this.tasksByColumn().get(columnId)?.length ?? 0;
    const limit = this.columnTaskLimits().get(columnId) ?? this.COLUMN_TASK_LIMIT;
    return total - limit;
  }

  expandColumn(columnId: number): void {
    this.columnTaskLimits.update(map => {
      const m = new Map(map);
      const current = m.get(columnId) ?? this.COLUMN_TASK_LIMIT;
      m.set(columnId, current + this.COLUMN_TASK_INCREMENT);
      return m;
    });
  }

  groupedTasksForColumn(columnId: number): { label: string; tasks: Task[] }[] {
    return groupTasksByMode(this.tasksForColumn(columnId), this.groupBy(), id => this.contactName(id), this.translate);
  }

  createColumn(title: string): void {
    const trimmed = title.trim();
    if (!trimmed) return;
    this.columnsApi.create(this.boardId(), trimmed).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: col => this.columns.update(c => c.some(x => x.id === col.id) ? c : [...c, col]),
    });
  }

  renameBoard(title: string): void {
    const trimmed = title.trim();
    if (!trimmed) { this.editingBoardTitle.set(false); return; }
    this.boardsApi.patch(this.boardId(), { title: trimmed }).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: updated => { this.board.set(updated); this.editingBoardTitle.set(false); },
    });
  }

  taskCountForColumn(columnId: number): number {
    return this.taskCountByColumn().get(columnId) ?? 0;
  }

  isOverWipLimit(column: Column): boolean {
    return column.wip_limit !== null && this.taskCountForColumn(column.id) > column.wip_limit;
  }

  setWipLimit(id: number, value: number | null): void {
    this.columnsApi.patch(id, { wip_limit: value }).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: updated => this.columns.update(cols => cols.map(c => c.id === id ? updated : c)),
    });
  }

  renameColumn(id: number, title: string): void {
    const trimmed = title.trim();
    if (!trimmed) { this.editingColumnId.set(null); return; }
    this.columnsApi.patch(id, { title: trimmed }).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: updated => { this.columns.update(cols => cols.map(c => c.id === id ? updated : c)); this.editingColumnId.set(null); },
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
        this.toast.show(this.translate.instant('TOAST.COLUMN_DELETED'));
      },
    });
  }

  createTask(payload: CreateTaskPayload): void {
    this.tasksApi.create(this.boardId(), payload).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: task => {
        this.tasks.update(t => t.some(x => x.id === task.id) ? t : [...t, task]);
        this.addingTaskForColumn.set(null);
        this.toast.show(this.translate.instant('TOAST.TASK_CREATED'));
      },
    });
  }

  onTaskUpdated(updated: Task): void {
    this.tasks.update(t => t.map(task => task.id === updated.id ? updated : task));
  }

  onTaskDeleted(id: number): void {
    this.tasks.update(t => t.filter(task => task.id !== id));
  }

  onTaskCreated(task: Task): void {
    this.tasks.update(t => t.some(x => x.id === task.id) ? t : [...t, task]);
  }

  confirmDeleteTask(): void {
    const id = this.pendingDeleteTaskId();
    if (id === null) return;
    this.tasksApi.delete(id).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: () => {
        this.tasks.update(t => t.filter(task => task.id !== id));
        this.pendingDeleteTaskId.set(null);
        this.toast.show(this.translate.instant('TOAST.TASK_DELETED'));
      },
    });
  }

  dropColumn(event: CdkDragDrop<Column[]>): void {
    handleColumnDrop(this.columns, this.columnsApi, this.toast, this.translate, this.destroyRef, event);
  }

  drop(event: CdkDragDrop<Task[]>, targetColumnId: number): void {
    handleTaskDrop(this.tasks, col => this.tasksForColumn(col), this.tasksApi, this.toast, this.translate, this.destroyRef, event, targetColumnId);
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
    bulkMoveTasks(this.selectedTaskIds, this.bulkMoveTarget, this.tasks, this.tasksApi, this.toast, this.translate, this.destroyRef);
  }

  confirmBulkDelete(): void {
    bulkDeleteTasks(this.selectedTaskIds, this.pendingBulkDelete, this.tasks, this.tasksApi, this.toast, this.translate, this.destroyRef);
  }

  priorityClass(priority: string): string {
    return `priority-${priority}`;
  }

  isOverdue(dueDate: string | null): boolean {
    return isOverdue(dueDate);
  }

  isSoon(dueDate: string | null): boolean {
    return isSoon(dueDate);
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
        if (this.pendingTaskId) {
          const task = tasks.find(t => t.id === this.pendingTaskId);
          if (task) this.selectedTask.set(task);
          this.pendingTaskId = null;
        }
      },
      error: () => { this.loading.set(false); },
    });
  }
}
