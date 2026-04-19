import { ChangeDetectionStrategy, Component, DestroyRef, inject, signal, OnInit } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { ActivatedRoute, RouterModule } from '@angular/router';
import { forkJoin } from 'rxjs';
import { ChartData, ChartOptions } from 'chart.js';
import { BaseChartDirective } from 'ng2-charts';
import { BoardsApiService } from '../../../../core/boards/boards-api.service';
import { ColumnsApiService, Column } from '../../../../core/columns/columns-api.service';
import { TasksApiService, Task } from '../../../../core/tasks/tasks-api.service';
import { ActivityApiService, ActivityEntry } from '../../../../core/activity/activity-api.service';
import { ContactsApiService, Contact } from '../../../../core/contacts/contacts-api.service';
import { BRAND_COLOR, PRIORITY_COLORS } from '../../../../shared/constants/colors';

@Component({
  selector: 'app-board-stats-page',
  standalone: true,
  imports: [BaseChartDirective, RouterModule],
  templateUrl: './board-stats-page.component.html',
  styleUrl: './board-stats-page.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class BoardStatsPageComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly destroyRef = inject(DestroyRef);
  private readonly boardsApi = inject(BoardsApiService);
  private readonly columnsApi = inject(ColumnsApiService);
  private readonly tasksApi = inject(TasksApiService);
  private readonly activityApi = inject(ActivityApiService);
  private readonly contactsApi = inject(ContactsApiService);

  boardId = 0;
  boardTitle = signal('Board');
  loading = signal(true);

  totalTasks = signal(0);
  doneTasks = signal(0);
  overdueTasks = signal(0);
  avgSubtaskCompletion = signal(0);

  columnChartData = signal<ChartData<'bar'>>({ labels: [], datasets: [] });
  priorityChartData = signal<ChartData<'doughnut'>>({ labels: [], datasets: [] });
  creationChartData = signal<ChartData<'line'>>({ labels: [], datasets: [] });
  activityChartData = signal<ChartData<'bar'>>({ labels: [], datasets: [] });
  assigneeChartData = signal<ChartData<'bar'>>({ labels: [], datasets: [] });

  barOptions: ChartOptions<'bar'> = {
    responsive: true,
    plugins: { legend: { display: false } },
    scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } },
  };

  doughnutOptions: ChartOptions<'doughnut'> = {
    responsive: true,
    plugins: { legend: { position: 'bottom' } },
  };

  lineOptions: ChartOptions<'line'> = {
    responsive: true,
    plugins: { legend: { display: false } },
    scales: {
      y: { beginAtZero: true, ticks: { stepSize: 1 } },
      x: { ticks: { maxRotation: 45 } },
    },
  };

  horizontalBarOptions: ChartOptions<'bar'> = {
    responsive: true,
    indexAxis: 'y',
    plugins: { legend: { display: false } },
    scales: { x: { beginAtZero: true, ticks: { stepSize: 1 } } },
  };

  ngOnInit(): void {
    this.boardId = Number(this.route.snapshot.paramMap.get('id'));
    this.boardsApi.getById(this.boardId)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe(b => this.boardTitle.set(b.title));

    forkJoin([
      this.columnsApi.getByBoard(this.boardId),
      this.tasksApi.getByBoard(this.boardId),
      this.activityApi.getByBoard(this.boardId),
      this.contactsApi.getAll(),
    ]).pipe(takeUntilDestroyed(this.destroyRef)).subscribe(([columns, tasks, activity, contacts]) => {
      this.buildKpis(columns, tasks);
      this.buildColumnChart(columns, tasks);
      this.buildPriorityChart(tasks);
      this.buildCreationChart(tasks);
      this.buildActivityChart(activity);
      this.buildAssigneeChart(tasks, contacts);
      this.loading.set(false);
    });
  }

  private buildKpis(columns: Column[], tasks: Task[]): void {
    this.totalTasks.set(tasks.length);
    const today = new Date(new Date().toDateString());
    this.overdueTasks.set(tasks.filter(t => t.due_date && new Date(t.due_date) < today).length);

    const lastCol = columns.length > 0 ? columns[columns.length - 1] : null;
    this.doneTasks.set(lastCol ? tasks.filter(t => t.column === lastCol.id).length : 0);

    const withSubtasks = tasks.filter(t => t.subtask_count > 0);
    if (withSubtasks.length > 0) {
      const avg = withSubtasks.reduce((sum, t) => sum + (t.subtask_done_count / t.subtask_count) * 100, 0) / withSubtasks.length;
      this.avgSubtaskCompletion.set(Math.round(avg));
    }
  }

  private buildColumnChart(columns: Column[], tasks: Task[]): void {
    this.columnChartData.set({
      labels: columns.map(c => c.title),
      datasets: [{
        data: columns.map(c => tasks.filter(t => t.column === c.id).length),
        backgroundColor: BRAND_COLOR,
        borderRadius: 6,
      }],
    });
  }

  private buildPriorityChart(tasks: Task[]): void {
    const priorities = ['urgent', 'high', 'medium', 'low'];
    this.priorityChartData.set({
      labels: priorities.map(p => p.charAt(0).toUpperCase() + p.slice(1)),
      datasets: [{
        data: priorities.map(p => tasks.filter(t => t.priority === p).length),
        backgroundColor: priorities.map(p => PRIORITY_COLORS[p]),
      }],
    });
  }

  private buildCreationChart(tasks: Task[]): void {
    const dayCounts = new Map<string, number>();
    for (const t of tasks) {
      const day = t.created_at.slice(0, 10);
      dayCounts.set(day, (dayCounts.get(day) ?? 0) + 1);
    }
    const sorted = [...dayCounts.entries()].sort((a, b) => a[0].localeCompare(b[0]));
    this.creationChartData.set({
      labels: sorted.map(([d]) => d),
      datasets: [{
        data: sorted.map(([, c]) => c),
        borderColor: BRAND_COLOR,
        backgroundColor: BRAND_COLOR + '33',
        fill: true,
        tension: 0.3,
        pointRadius: 4,
      }],
    });
  }

  private buildActivityChart(activity: ActivityEntry[]): void {
    const dayCounts = new Map<string, number>();
    for (const a of activity) {
      const day = a.created_at.slice(0, 10);
      dayCounts.set(day, (dayCounts.get(day) ?? 0) + 1);
    }
    const sorted = [...dayCounts.entries()].sort((a, b) => a[0].localeCompare(b[0]));
    this.activityChartData.set({
      labels: sorted.map(([d]) => d),
      datasets: [{
        data: sorted.map(([, c]) => c),
        backgroundColor: BRAND_COLOR + '99',
        borderRadius: 4,
      }],
    });
  }

  private buildAssigneeChart(tasks: Task[], contacts: Contact[]): void {
    const contactMap = new Map(contacts.map(c => [c.id, `${c.first_name} ${c.last_name}`]));
    const assigneeCounts = new Map<string, number>();
    for (const t of tasks) {
      const name = t.assigned_to ? (contactMap.get(t.assigned_to) ?? 'Unknown') : 'Unassigned';
      assigneeCounts.set(name, (assigneeCounts.get(name) ?? 0) + 1);
    }
    const sorted = [...assigneeCounts.entries()].sort((a, b) => b[1] - a[1]);
    this.assigneeChartData.set({
      labels: sorted.map(([n]) => n),
      datasets: [{
        data: sorted.map(([, c]) => c),
        backgroundColor: BRAND_COLOR,
        borderRadius: 6,
      }],
    });
  }
}
