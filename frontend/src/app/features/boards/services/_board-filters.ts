import { WritableSignal, Signal, computed, DestroyRef } from '@angular/core';
import { takeUntilDestroyed, toObservable } from '@angular/core/rxjs-interop';
import { ActivatedRoute, Router } from '@angular/router';
import { debounceTime, skip } from 'rxjs';
import { Task } from '../../../core/tasks/tasks-api.service';

export type SavedFilter = {
  name: string;
  priority: string;
  assignee: number | '';
  due: 'overdue' | 'soon' | '';
  search: string;
};

export function restoreFiltersFromUrl(
  route: ActivatedRoute,
  searchQuery: WritableSignal<string>,
  filterPriority: WritableSignal<string>,
  filterAssignee: WritableSignal<number | ''>,
  filterDue: WritableSignal<'overdue' | 'soon' | ''>,
  groupBy: WritableSignal<'none' | 'priority' | 'assignee'>,
  skipUrlSync: { value: boolean },
): void {
  const params = route.snapshot.queryParams;
  skipUrlSync.value = true;
  if (params['search']) searchQuery.set(params['search']);
  if (params['priority']) filterPriority.set(params['priority']);
  if (params['assignee']) filterAssignee.set(Number(params['assignee']));
  if (params['due']) filterDue.set(params['due'] as 'overdue' | 'soon');
  if (params['groupBy']) groupBy.set(params['groupBy'] as 'priority' | 'assignee');
  skipUrlSync.value = false;
}

export function createFilterUrlSync(
  router: Router,
  route: ActivatedRoute,
  searchQuery: Signal<string>,
  filterPriority: Signal<string>,
  filterAssignee: Signal<number | ''>,
  filterDue: Signal<'overdue' | 'soon' | ''>,
  groupBy: Signal<'none' | 'priority' | 'assignee'>,
  skipUrlSync: { value: boolean },
  destroyRef: DestroyRef,
): void {
  const params$ = toObservable(computed(() => {
    const search = searchQuery();
    const priority = filterPriority();
    const assignee = filterAssignee();
    const due = filterDue();
    const gb = groupBy();
    return { search, priority, assignee, due, gb };
  }));

  params$.pipe(
    skip(1),
    debounceTime(0),
    takeUntilDestroyed(destroyRef),
  ).subscribe(({ search, priority, assignee, due, gb }) => {
    if (skipUrlSync.value) return;

    const params: Record<string, string> = {};
    if (search) params['search'] = search;
    if (priority) params['priority'] = priority;
    if (assignee) params['assignee'] = String(assignee);
    if (due) params['due'] = due;
    if (gb !== 'none') params['groupBy'] = gb;

    router.navigate([], { queryParams: params, replaceUrl: true, relativeTo: route });
  });
}

export function filterTasks(
  tasks: Task[],
  searchQuery: string,
  filterPriority: string,
  filterAssignee: number | '',
  filterDue: 'overdue' | 'soon' | '',
): Task[] {
  const q = searchQuery.trim().toLowerCase();
  return tasks.filter(t => {
    if (q && !t.title.toLowerCase().includes(q)) return false;
    if (filterPriority && t.priority !== filterPriority) return false;
    if (filterAssignee !== '' && !t.assigned_to.includes(filterAssignee as number)) return false;
    if (filterDue === 'overdue' && !isOverdue(t.due_date)) return false;
    if (filterDue === 'soon' && !(isSoon(t.due_date) && !isOverdue(t.due_date))) return false;
    return true;
  });
}

export function loadSavedFilters(boardId: number): SavedFilter[] {
  const raw = localStorage.getItem(`board-filters-${boardId}`);
  if (!raw) return [];
  try { return JSON.parse(raw); }
  catch { return []; }
}

export function persistSavedFilters(boardId: number, filters: SavedFilter[]): void {
  localStorage.setItem(`board-filters-${boardId}`, JSON.stringify(filters));
}

export function isOverdue(dueDate: string | null): boolean {
  if (!dueDate) return false;
  return new Date(dueDate) < new Date(new Date().toDateString());
}

export function isSoon(dueDate: string | null): boolean {
  if (!dueDate) return false;
  const today = new Date(new Date().toDateString());
  const due = new Date(dueDate);
  const diff = (due.getTime() - today.getTime()) / (1000 * 60 * 60 * 24);
  return diff >= 0 && diff <= 3;
}
