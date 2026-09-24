import { ChangeDetectionStrategy, Component, DestroyRef, ElementRef, HostListener, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { RouterModule } from '@angular/router';
import { TranslateModule, TranslateService } from '@ngx-translate/core';
import { BoardsApiService } from '../../../../core/boards/boards-api.service';
import { ToastService } from '../../../../shared/services/toast.service';
import { BoardStateService } from '../../services/board-state.service';

@Component({
  selector: 'app-board-more-menu',
  imports: [RouterModule, TranslateModule],
  templateUrl: './board-more-menu.component.html',
  styleUrl: './board-more-menu.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class BoardMoreMenuComponent {
  private readonly boardsApi = inject(BoardsApiService);
  private readonly toast = inject(ToastService);
  private readonly translate = inject(TranslateService);
  private readonly destroyRef = inject(DestroyRef);
  private readonly elementRef = inject(ElementRef);
  protected readonly state = inject(BoardStateService);

  open = signal(false);

  @HostListener('document:click', ['$event'])
  onDocumentClick(event: Event): void {
    if (!this.elementRef.nativeElement.contains(event.target)) {
      this.open.set(false);
    }
  }

  toggle(): void {
    this.open.update(v => !v);
  }

  shareInviteLink(): void {
    this.open.set(false);
    this.boardsApi.createInviteLink(this.state.boardId())
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: res => {
          const url = `${window.location.origin}/boards/join/${res.token}`;
          navigator.clipboard.writeText(url).then(() => {
            this.toast.show(this.translate.instant('INVITE.LINK_COPIED'));
          });
        },
      });
  }

  exportCsv(): void {
    this.open.set(false);
    this.boardsApi.exportCsv(this.state.boardId()).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: blob => this.downloadBlob(blob, `board-${this.state.boardId()}.csv`),
    });
  }

  exportPdf(): void {
    this.open.set(false);
    this.boardsApi.exportPdf(this.state.boardId()).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: blob => this.downloadBlob(blob, `board-${this.state.boardId()}.pdf`),
    });
  }

  importCsv(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) return;
    this.open.set(false);
    this.boardsApi.importCsv(this.state.boardId(), file).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: (res) => {
        this.toast.show(this.translate.instant('BOARD_DETAIL.IMPORT_SUCCESS', { count: res.imported }));
        this.state.reload();
      },
      error: (err) => this.toast.show(err?.error?.detail ?? this.translate.instant('BOARD_DETAIL.IMPORT_FAILED'), 'error'),
    });
    input.value = '';
  }

  private downloadBlob(blob: Blob, filename: string): void {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  }
}
