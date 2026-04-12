import { Component, inject, signal, OnInit } from '@angular/core';
import { ActivatedRoute, RouterModule } from '@angular/router';
import { ChartData, ChartOptions } from 'chart.js';
import { BaseChartDirective } from 'ng2-charts';
import { BoardsApiService } from '../../../../core/boards/boards-api.service';
import { ColumnsApiService, Column } from '../../../../core/columns/columns-api.service';
import { TasksApiService, Task } from '../../../../core/tasks/tasks-api.service';

@Component({
  selector: 'app-board-stats-page',
  standalone: true,
  imports: [BaseChartDirective, RouterModule],
  templateUrl: './board-stats-page.component.html',
  styleUrl: './board-stats-page.component.scss',
})
export class BoardStatsPageComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly boardsApi = inject(BoardsApiService);
  private readonly columnsApi = inject(ColumnsApiService);
  private readonly tasksApi = inject(TasksApiService);

  boardId = 0;
  boardTitle = signal('Board');
  loading = signal(true);

  columnChartData = signal<ChartData<'bar'>>({ labels: [], datasets: [] });
  priorityChartData = signal<ChartData<'doughnut'>>({ labels: [], datasets: [] });

  barOptions: ChartOptions<'bar'> = {
    responsive: true,
    plugins: { legend: { display: false } },
    scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } },
  };

  doughnutOptions: ChartOptions<'doughnut'> = {
    responsive: true,
    plugins: { legend: { position: 'bottom' } },
  };

  totalTasks = signal(0);
  overdueTasks = signal(0);

  ngOnInit(): void {
    this.boardId = Number(this.route.snapshot.paramMap.get('id'));
    this.boardsApi.getById(this.boardId).subscribe(b => this.boardTitle.set(b.title));

    this.columnsApi.getByBoard(this.boardId).subscribe(columns => {
      this.tasksApi.getByBoard(this.boardId).subscribe(tasks => {
        this.buildCharts(columns, tasks);
        this.loading.set(false);
      });
    });
  }

  private buildCharts(columns: Column[], tasks: Task[]): void {
    this.totalTasks.set(tasks.length);
    const today = new Date(new Date().toDateString());
    this.overdueTasks.set(tasks.filter(t => t.due_date && new Date(t.due_date) < today).length);

    this.columnChartData.set({
      labels: columns.map(c => c.title),
      datasets: [{
        data: columns.map(c => tasks.filter(t => t.column === c.id).length),
        backgroundColor: '#29abe2',
        borderRadius: 6,
      }],
    });

    const priorityColors: Record<string, string> = {
      urgent: '#ff3d00', high: '#ff3d00', medium: '#ffa800', low: '#7ae229',
    };
    const priorities = ['urgent', 'high', 'medium', 'low'];
    this.priorityChartData.set({
      labels: priorities.map(p => p.charAt(0).toUpperCase() + p.slice(1)),
      datasets: [{
        data: priorities.map(p => tasks.filter(t => t.priority === p).length),
        backgroundColor: priorities.map(p => priorityColors[p]),
      }],
    });
  }
}
