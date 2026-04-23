import { ChangeDetectionStrategy, Component, DestroyRef, inject, signal, OnInit } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { ActivatedRoute, RouterModule } from '@angular/router';
import { DatePipe } from '@angular/common';
import { TranslateModule, TranslateService } from '@ngx-translate/core';
import { BoardsApiService } from '../../../../core/boards/boards-api.service';
import { TasksApiService, Task } from '../../../../core/tasks/tasks-api.service';
import { ToastService } from '../../../../shared/services/toast.service';

@Component({
  selector: 'app-board-archive-page',
  standalone: true,
  imports: [RouterModule, DatePipe, TranslateModule],
  templateUrl: './board-archive-page.component.html',
  styleUrl: './board-archive-page.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class BoardArchivePageComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly destroyRef = inject(DestroyRef);
  private readonly boardsApi = inject(BoardsApiService);
  private readonly tasksApi = inject(TasksApiService);
  private readonly toast = inject(ToastService);
  private readonly translate = inject(TranslateService);

  boardId = 0;
  boardTitle = signal('Board');
  loading = signal(true);
  tasks = signal<Task[]>([]);

  ngOnInit(): void {
    this.boardId = Number(this.route.snapshot.paramMap.get('id'));
    this.boardsApi.getById(this.boardId)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe(b => this.boardTitle.set(b.title));

    this.loadArchive();
  }

  restore(task: Task): void {
    this.tasksApi.restore(task.id).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: () => {
        this.tasks.update(list => list.filter(t => t.id !== task.id));
        this.toast.show(this.translate.instant('TOAST.TASK_RESTORED'));
      },
      error: () => this.toast.show(this.translate.instant('TOAST.FAILED_RESTORE_TASK'), 'error'),
    });
  }

  private loadArchive(): void {
    this.tasksApi.getArchive(this.boardId)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: tasks => {
          this.tasks.set(tasks);
          this.loading.set(false);
        },
        error: () => {
          this.toast.show(this.translate.instant('TOAST.FAILED_LOAD_ARCHIVE'), 'error');
          this.loading.set(false);
        },
      });
  }
}
