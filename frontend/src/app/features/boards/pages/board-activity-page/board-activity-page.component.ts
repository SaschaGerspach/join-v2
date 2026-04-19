import { ChangeDetectionStrategy, Component, DestroyRef, inject, signal, OnInit } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { ActivatedRoute, RouterModule } from '@angular/router';
import { DatePipe } from '@angular/common';
import { BoardsApiService } from '../../../../core/boards/boards-api.service';
import { ActivityApiService, ActivityEntry } from '../../../../core/activity/activity-api.service';

@Component({
  selector: 'app-board-activity-page',
  standalone: true,
  imports: [RouterModule, DatePipe],
  templateUrl: './board-activity-page.component.html',
  styleUrl: './board-activity-page.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class BoardActivityPageComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly destroyRef = inject(DestroyRef);
  private readonly boardsApi = inject(BoardsApiService);
  private readonly activityApi = inject(ActivityApiService);

  boardId = 0;
  boardTitle = signal('Board');
  loading = signal(true);
  entries = signal<ActivityEntry[]>([]);

  ngOnInit(): void {
    this.boardId = Number(this.route.snapshot.paramMap.get('id'));
    this.boardsApi.getById(this.boardId)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe(b => this.boardTitle.set(b.title));

    this.activityApi.getByBoard(this.boardId)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe(entries => {
        this.entries.set(entries);
        this.loading.set(false);
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
