import { ChangeDetectionStrategy, Component, DestroyRef, inject, signal, OnInit } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { ActivatedRoute, RouterModule } from '@angular/router';
import { DatePipe } from '@angular/common';
import { TranslateModule, TranslateService } from '@ngx-translate/core';
import { BoardsApiService } from '../../../../core/boards/boards-api.service';
import { ActivityApiService, ActivityEntry } from '../../../../core/activity/activity-api.service';
import { ToastService } from '../../../../shared/services/toast.service';

@Component({
  selector: 'app-board-activity-page',
  standalone: true,
  imports: [RouterModule, DatePipe, TranslateModule],
  templateUrl: './board-activity-page.component.html',
  styleUrl: './board-activity-page.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class BoardActivityPageComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly destroyRef = inject(DestroyRef);
  private readonly boardsApi = inject(BoardsApiService);
  private readonly activityApi = inject(ActivityApiService);
  private readonly toast = inject(ToastService);
  private readonly translate = inject(TranslateService);

  boardId = signal(0);
  boardTitle = signal('Board');
  loading = signal(true);
  entries = signal<ActivityEntry[]>([]);

  ngOnInit(): void {
    this.boardId.set(Number(this.route.snapshot.paramMap.get('id')));
    this.boardsApi.getById(this.boardId())
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: b => this.boardTitle.set(b.title),
        error: () => this.toast.show(this.translate.instant('TOAST.SOMETHING_WRONG'), 'error'),
      });

    this.activityApi.getByBoard(this.boardId())
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: entries => { this.entries.set(entries); this.loading.set(false); },
        error: () => { this.loading.set(false); this.toast.show(this.translate.instant('TOAST.SOMETHING_WRONG'), 'error'); },
      });
  }

  actionLabel(entry: ActivityEntry): string {
    const labels: Record<string, string> = {
      created: 'created',
      updated: 'updated',
      deleted: 'deleted',
      moved: 'moved',
    };
    return labels[entry.action] ?? entry.action;
  }

  entityIcon(entry: ActivityEntry): string {
    const icons: Record<string, string> = {
      task: '\u{1F4CB}',
      column: '\u{1F4CA}',
      comment: '\u{1F4AC}',
    };
    return icons[entry.entity_type] ?? '';
  }
}
