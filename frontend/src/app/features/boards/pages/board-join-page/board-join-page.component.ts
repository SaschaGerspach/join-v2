import { ChangeDetectionStrategy, Component, DestroyRef, OnInit, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { ActivatedRoute, Router } from '@angular/router';
import { TranslateModule, TranslateService } from '@ngx-translate/core';
import { BoardsApiService } from '../../../../core/boards/boards-api.service';
import { LoadingSpinnerComponent } from '../../../../shared/components/loading-spinner/loading-spinner.component';
import { ToastService } from '../../../../shared/services/toast.service';

@Component({
  selector: 'app-board-join-page',
  standalone: true,
  imports: [TranslateModule, LoadingSpinnerComponent],
  template: `
    <div class="join-page">
      @if (loading()) {
        <app-loading-spinner />
      } @else if (error()) {
        <div class="join-message error">
          <h2>{{ 'INVITE.INVALID_LINK' | translate }}</h2>
          <p>{{ 'INVITE.LINK_EXPIRED' | translate }}</p>
        </div>
      }
    </div>
  `,
  styles: [`
    .join-page { display: flex; align-items: center; justify-content: center; min-height: 50vh; }
    .join-message { text-align: center; }
    .join-message h2 { font-size: 1.4rem; margin-bottom: 0.5rem; color: var(--color-text); }
    .join-message p { color: var(--color-muted); }
  `],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class BoardJoinPageComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly boardsApi = inject(BoardsApiService);
  private readonly toast = inject(ToastService);
  private readonly translate = inject(TranslateService);
  private readonly destroyRef = inject(DestroyRef);

  loading = signal(true);
  error = signal(false);

  ngOnInit(): void {
    const token = this.route.snapshot.paramMap.get('token')!;
    this.boardsApi.joinViaLink(token)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: res => {
          this.toast.show(
            res.already_member
              ? this.translate.instant('INVITE.ALREADY_MEMBER', { board: res.board_title })
              : this.translate.instant('INVITE.JOINED', { board: res.board_title })
          );
          this.router.navigate(['/boards', res.board_id]);
        },
        error: () => {
          this.loading.set(false);
          this.error.set(true);
        },
      });
  }
}
