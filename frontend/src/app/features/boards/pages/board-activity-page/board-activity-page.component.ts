import { ChangeDetectionStrategy, Component, inject, signal, OnInit } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { RouterModule } from '@angular/router';
import { DatePipe } from '@angular/common';
import { TranslateModule } from '@ngx-translate/core';
import { ActivityApiService, ActivityEntry } from '../../../../core/activity/activity-api.service';
import { initBoardPage } from '../../utils/board-page-init';

@Component({
  selector: 'app-board-activity-page',
  standalone: true,
  imports: [RouterModule, DatePipe, TranslateModule],
  templateUrl: './board-activity-page.component.html',
  styleUrl: './board-activity-page.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class BoardActivityPageComponent implements OnInit {
  protected readonly board = initBoardPage();
  private readonly activityApi = inject(ActivityApiService);

  loading = signal(true);
  entries = signal<ActivityEntry[]>([]);

  ngOnInit(): void {
    this.activityApi.getByBoard(this.board.boardId())
      .pipe(takeUntilDestroyed(this.board.destroyRef))
      .subscribe({
        next: entries => { this.entries.set(entries); this.loading.set(false); },
        error: () => { this.loading.set(false); },
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
