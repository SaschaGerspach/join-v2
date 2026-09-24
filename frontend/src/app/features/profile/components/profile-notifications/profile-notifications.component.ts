import { ChangeDetectionStrategy, Component, DestroyRef, OnInit, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { TranslateModule } from '@ngx-translate/core';
import { NotificationsApiService } from '../../../../core/notifications/notifications-api.service';
import { Board, BoardsApiService } from '../../../../core/boards/boards-api.service';

type EmailDelivery = 'instant' | 'digest' | 'none';

@Component({
  selector: 'app-profile-notifications',
  imports: [TranslateModule],
  templateUrl: './profile-notifications.component.html',
  styleUrl: './profile-notifications.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ProfileNotificationsComponent implements OnInit {
  private readonly notificationsApi = inject(NotificationsApiService);
  private readonly boardsApi = inject(BoardsApiService);
  private readonly destroyRef = inject(DestroyRef);

  boards = signal<Board[]>([]);
  disabledTypes = signal<Set<string>>(new Set());
  mutedBoardIds = signal<Set<number>>(new Set());
  emailDelivery = signal<EmailDelivery>('instant');

  ngOnInit(): void {
    this.notificationsApi.getPreferences().pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: prefs => {
        this.disabledTypes.set(new Set(prefs.disabled_types));
        this.mutedBoardIds.set(new Set(prefs.muted_boards));
        this.emailDelivery.set(prefs.email_delivery);
      },
    });

    this.boardsApi.getAll().pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: boards => this.boards.set(boards),
    });
  }

  toggleType(type: string): void {
    const types = new Set(this.disabledTypes());
    if (types.has(type)) {
      types.delete(type);
    } else {
      types.add(type);
    }
    this.disabledTypes.set(types);
    this.savePreferences();
  }

  setEmailDelivery(value: EmailDelivery): void {
    this.emailDelivery.set(value);
    this.savePreferences();
  }

  toggleMuteBoard(boardId: number): void {
    const muted = new Set(this.mutedBoardIds());
    if (muted.has(boardId)) {
      muted.delete(boardId);
    } else {
      muted.add(boardId);
    }
    this.mutedBoardIds.set(muted);
    this.savePreferences();
  }

  private savePreferences(): void {
    this.notificationsApi.updatePreferences({
      disabled_types: [...this.disabledTypes()],
      muted_boards: [...this.mutedBoardIds()],
      email_delivery: this.emailDelivery(),
    }).pipe(takeUntilDestroyed(this.destroyRef)).subscribe();
  }
}
