import { ChangeDetectionStrategy, Component, inject, signal, OnInit } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { RouterModule } from '@angular/router';
import { DatePipe } from '@angular/common';
import { TranslateModule, TranslateService } from '@ngx-translate/core';
import { TasksApiService, Task } from '../../../../core/tasks/tasks-api.service';
import { ToastService } from '../../../../shared/services/toast.service';
import { initBoardPage } from '../../utils/board-page-init';

@Component({
  selector: 'app-board-archive-page',
  standalone: true,
  imports: [RouterModule, DatePipe, TranslateModule],
  templateUrl: './board-archive-page.component.html',
  styleUrl: './board-archive-page.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class BoardArchivePageComponent implements OnInit {
  protected readonly board = initBoardPage();
  private readonly tasksApi = inject(TasksApiService);
  private readonly toast = inject(ToastService);
  private readonly translate = inject(TranslateService);

  loading = signal(true);
  tasks = signal<Task[]>([]);

  ngOnInit(): void {
    this.loadArchive();
  }

  restore(task: Task): void {
    this.tasksApi.restore(task.id).pipe(takeUntilDestroyed(this.board.destroyRef)).subscribe({
      next: () => {
        this.tasks.update(list => list.filter(t => t.id !== task.id));
        this.toast.show(this.translate.instant('TOAST.TASK_RESTORED'));
      },
    });
  }

  private loadArchive(): void {
    this.tasksApi.getArchive(this.board.boardId())
      .pipe(takeUntilDestroyed(this.board.destroyRef))
      .subscribe({
        next: tasks => {
          this.tasks.set(tasks);
          this.loading.set(false);
        },
        error: () => {
          this.loading.set(false);
        },
      });
  }
}
