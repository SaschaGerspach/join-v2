import { ChangeDetectionStrategy, Component, inject, signal, OnInit } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { RouterModule } from '@angular/router';
import { ChartData, ChartOptions } from 'chart.js';
import { TranslateModule } from '@ngx-translate/core';
import { BaseChartDirective, provideCharts, withDefaultRegisterables } from 'ng2-charts';
import { BoardsApiService, TimeReport } from '../../../../core/boards/boards-api.service';
import { BRAND_COLOR } from '../../../../shared/constants/colors';
import { initBoardPage } from '../../utils/board-page-init';

@Component({
  selector: 'app-board-time-report-page',
  standalone: true,
  imports: [BaseChartDirective, RouterModule, TranslateModule],
  providers: [provideCharts(withDefaultRegisterables())],
  templateUrl: './board-time-report-page.component.html',
  styleUrl: './board-time-report-page.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class BoardTimeReportPageComponent implements OnInit {
  protected readonly board = initBoardPage();
  private readonly boardsApi = inject(BoardsApiService);
  loading = signal(true);

  totalHours = signal('0');
  totalEntries = signal(0);

  userChartData = signal<ChartData<'bar'>>({ labels: [], datasets: [] });
  taskChartData = signal<ChartData<'bar'>>({ labels: [], datasets: [] });
  dailyChartData = signal<ChartData<'line'>>({ labels: [], datasets: [] });

  horizontalBarOptions: ChartOptions<'bar'> = {
    responsive: true,
    indexAxis: 'y',
    plugins: { legend: { display: false } },
    scales: { x: { beginAtZero: true, title: { display: true, text: 'Hours' } } },
  };

  lineOptions: ChartOptions<'line'> = {
    responsive: true,
    plugins: { legend: { display: false } },
    scales: {
      y: { beginAtZero: true, title: { display: true, text: 'Hours' } },
      x: { ticks: { maxRotation: 45 } },
    },
  };

  ngOnInit(): void {
    this.boardsApi.getTimeReport(this.board.boardId())
      .pipe(takeUntilDestroyed(this.board.destroyRef))
      .subscribe({
        next: (report) => {
          this.buildKpis(report);
          this.buildUserChart(report);
          this.buildTaskChart(report);
          this.buildDailyChart(report);
          this.loading.set(false);
        },
        error: () => this.loading.set(false),
      });
  }

  private buildKpis(report: TimeReport): void {
    this.totalHours.set((report.total_minutes / 60).toFixed(1));
    this.totalEntries.set(report.per_user.length + report.per_task.length);
  }

  private buildUserChart(report: TimeReport): void {
    this.userChartData.set({
      labels: report.per_user.map(u => u.name),
      datasets: [{
        data: report.per_user.map(u => +(u.total_minutes / 60).toFixed(1)),
        backgroundColor: BRAND_COLOR,
        borderRadius: 6,
      }],
    });
  }

  private buildTaskChart(report: TimeReport): void {
    this.taskChartData.set({
      labels: report.per_task.map(t => t.title.length > 30 ? t.title.slice(0, 30) + '...' : t.title),
      datasets: [{
        data: report.per_task.map(t => +(t.total_minutes / 60).toFixed(1)),
        backgroundColor: BRAND_COLOR + '99',
        borderRadius: 6,
      }],
    });
  }

  private buildDailyChart(report: TimeReport): void {
    this.dailyChartData.set({
      labels: report.per_day.map(d => d.date),
      datasets: [{
        data: report.per_day.map(d => +(d.total_minutes / 60).toFixed(1)),
        borderColor: BRAND_COLOR,
        backgroundColor: BRAND_COLOR + '33',
        fill: true,
        tension: 0.3,
        pointRadius: 4,
      }],
    });
  }
}
