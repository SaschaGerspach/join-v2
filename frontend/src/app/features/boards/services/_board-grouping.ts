import { TranslateService } from '@ngx-translate/core';
import { Task } from '../../../core/tasks/tasks-api.service';

export function groupTasksByMode(
  tasks: Task[],
  mode: 'none' | 'priority' | 'assignee',
  contactName: (id: number) => string,
  translate: TranslateService,
): { label: string; tasks: Task[] }[] {
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
    const unassigned = translate.instant('BOARD_DETAIL.UNASSIGNED');
    groups.set(unassigned, []);
    order.push(unassigned);
    for (const t of tasks) {
      if (t.assigned_to.length === 0) {
        groups.get(unassigned)!.push(t);
      } else {
        for (const id of t.assigned_to) {
          const name = contactName(id) || translate.instant('BOARD_DETAIL.UNKNOWN');
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
