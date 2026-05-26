import { ChangeDetectionStrategy, Component, DestroyRef, inject, signal, computed, OnInit } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { TranslateModule } from '@ngx-translate/core';
import { TasksApiService, WorkloadTask, WorkloadContact } from '../../../../core/tasks/tasks-api.service';

type HeatmapCell = {
  date: string;
  count: number;
  tasks: WorkloadTask[];
};

type ContactRow = {
  contact: WorkloadContact;
  cells: HeatmapCell[];
  totalTasks: number;
};

@Component({
  selector: 'app-workload-page',
  standalone: true,
  imports: [TranslateModule],
  templateUrl: './workload-page.component.html',
  styleUrl: './workload-page.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class WorkloadPageComponent implements OnInit {
  private readonly tasksApi = inject(TasksApiService);
  private readonly destroyRef = inject(DestroyRef);

  loading = signal(true);
  contacts = signal<WorkloadContact[]>([]);
  tasks = signal<WorkloadTask[]>([]);
  weeksToShow = signal(12);
  hoveredCell = signal<{ contactId: number; date: string } | null>(null);

  dateColumns = computed(() => {
    const weeks = this.weeksToShow();
    const today = new Date();
    const start = new Date(today);
    start.setDate(start.getDate() - (weeks * 7) + 1);

    const dates: string[] = [];
    const current = new Date(start);
    while (current <= today) {
      dates.push(this.toDateString(current));
      current.setDate(current.getDate() + 1);
    }
    return dates;
  });

  weekLabels = computed(() => {
    const dates = this.dateColumns();
    const labels: { label: string; span: number }[] = [];
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

    let currentWeek = -1;
    for (const d of dates) {
      const date = new Date(d);
      const week = this.getWeekNumber(date);
      if (week !== currentWeek) {
        labels.push({ label: `${date.getDate()} ${months[date.getMonth()]}`, span: 1 });
        currentWeek = week;
      } else {
        labels[labels.length - 1].span++;
      }
    }
    return labels;
  });

  contactRows = computed<ContactRow[]>(() => {
    const allContacts = this.contacts();
    const allTasks = this.tasks();
    const dates = this.dateColumns();

    if (allContacts.length === 0 || dates.length === 0) return [];

    const tasksByContactDate = new Map<string, WorkloadTask[]>();

    for (const task of allTasks) {
      const start = task.start_date ? new Date(task.start_date) : null;
      const end = task.due_date ? new Date(task.due_date) : null;
      const rangeStart = start ?? end;
      const rangeEnd = end ?? start;
      if (!rangeStart || !rangeEnd) continue;

      const current = new Date(rangeStart);
      while (current <= rangeEnd) {
        const dateStr = this.toDateString(current);
        for (const contactId of task.assigned_to) {
          const key = `${contactId}_${dateStr}`;
          const list = tasksByContactDate.get(key) ?? [];
          list.push(task);
          tasksByContactDate.set(key, list);
        }
        current.setDate(current.getDate() + 1);
      }
    }

    return allContacts.map(contact => {
      const cells = dates.map(date => {
        const key = `${contact.id}_${date}`;
        const tasks = tasksByContactDate.get(key) ?? [];
        return { date, count: tasks.length, tasks };
      });
      const totalTasks = allTasks.filter(t => t.assigned_to.includes(contact.id)).length;
      return { contact, cells, totalTasks };
    }).sort((a, b) => b.totalTasks - a.totalTasks);
  });

  maxCount = computed(() => {
    let max = 0;
    for (const row of this.contactRows()) {
      for (const cell of row.cells) {
        if (cell.count > max) max = cell.count;
      }
    }
    return max || 1;
  });

  hoveredInfo = computed(() => {
    const h = this.hoveredCell();
    if (!h) return null;
    const row = this.contactRows().find(r => r.contact.id === h.contactId);
    if (!row) return null;
    const cell = row.cells.find(c => c.date === h.date);
    if (!cell || cell.count === 0) return null;
    return { contact: row.contact.name, date: h.date, tasks: cell.tasks };
  });

  ngOnInit(): void {
    this.tasksApi.getWorkload()
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: res => {
          this.contacts.set(res.contacts);
          this.tasks.set(res.tasks);
          this.loading.set(false);
        },
      });
  }

  cellIntensity(count: number): number {
    if (count === 0) return 0;
    const max = this.maxCount();
    return Math.ceil((count / max) * 4);
  }

  onCellHover(contactId: number, date: string): void {
    this.hoveredCell.set({ contactId, date });
  }

  onCellLeave(): void {
    this.hoveredCell.set(null);
  }

  setWeeks(weeks: number): void {
    this.weeksToShow.set(weeks);
  }

  isToday(date: string): boolean {
    return date === this.toDateString(new Date());
  }

  private toDateString(d: Date): string {
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
  }

  private getWeekNumber(d: Date): number {
    const oneJan = new Date(d.getFullYear(), 0, 1);
    return Math.ceil(((d.getTime() - oneJan.getTime()) / 86400000 + oneJan.getDay() + 1) / 7);
  }
}
