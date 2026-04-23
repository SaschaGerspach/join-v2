import { ChangeDetectionStrategy, Component, DestroyRef, inject, signal, computed, OnInit } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { NgTemplateOutlet } from '@angular/common';
import { BoardsApiService, Board, BoardMember, BoardMemberRole } from '../../../../core/boards/boards-api.service';
import { LoadingSpinnerComponent } from '../../../../shared/components/loading-spinner/loading-spinner.component';
import { ConfirmDialogComponent } from '../../../../shared/components/confirm-dialog/confirm-dialog.component';
import { ToastService } from '../../../../shared/services/toast.service';
import { TranslateModule } from '@ngx-translate/core';

@Component({
  selector: 'app-boards-page',
  standalone: true,
  imports: [FormsModule, NgTemplateOutlet, LoadingSpinnerComponent, ConfirmDialogComponent, TranslateModule],
  templateUrl: './boards-page.component.html',
  styleUrl: './boards-page.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class BoardsPageComponent implements OnInit {
  private readonly api = inject(BoardsApiService);
  private readonly router = inject(Router);
  private readonly toast = inject(ToastService);
  private readonly destroyRef = inject(DestroyRef);

  boards = signal<Board[]>([]);
  ownedBoards = computed(() => this.boards().filter(b => b.is_owner && b.is_member));
  sharedBoards = computed(() => this.boards().filter(b => !b.is_owner && b.is_member));
  adminBoards = computed(() => this.boards().filter(b => !b.is_member));
  newTitle = '';
  newTemplate = 'kanban';
  showForm = signal(false);
  loading = signal(true);
  pendingDeleteId = signal<number | null>(null);

  managingBoard = signal<Board | null>(null);
  members = signal<BoardMember[]>([]);
  inviteEmail = '';
  inviteError = signal('');
  pendingRemoveMemberId = signal<number | null>(null);

  ngOnInit(): void {
    this.loadBoards();
  }

  loadBoards(): void {
    this.loading.set(true);
    this.api.getAll().pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: boards => { this.boards.set(boards); this.loading.set(false); },
      error: () => { this.toast.show('Failed to load boards.', 'error'); this.loading.set(false); },
    });
  }

  createBoard(): void {
    const title = this.newTitle.trim();
    if (!title) return;

    this.api.create(title, this.newTemplate).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: board => {
        this.boards.update(b => [...b, board]);
        this.newTitle = '';
        this.newTemplate = 'kanban';
        this.showForm.set(false);
        this.toast.show('Board created');
      },
      error: () => this.toast.show('Failed to create board.', 'error'),
    });
  }

  openBoard(id: number): void {
    this.router.navigate(['/boards', id]);
  }

  deleteBoard(id: number, event: Event): void {
    event.stopPropagation();
    this.pendingDeleteId.set(id);
  }

  confirmDelete(): void {
    const id = this.pendingDeleteId();
    if (id === null) return;
    this.api.delete(id).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: () => {
        this.boards.update(b => b.filter(board => board.id !== id));
        this.pendingDeleteId.set(null);
        this.toast.show('Board deleted');
      },
      error: () => this.toast.show('Failed to delete board.', 'error'),
    });
  }

  openMembers(board: Board, event: Event): void {
    event.stopPropagation();
    this.managingBoard.set(board);
    this.inviteEmail = '';
    this.inviteError.set('');
    this.api.getMembers(board.id).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: m => this.members.set(m),
      error: () => this.members.set([]),
    });
  }

  invite(): void {
    const board = this.managingBoard();
    if (!board || !this.inviteEmail.trim()) return;
    this.inviteError.set('');
    this.api.inviteMember(board.id, this.inviteEmail.trim()).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: m => { this.members.update(list => [...list, m]); this.inviteEmail = ''; this.toast.show('Invitation sent'); },
      error: (err) => this.inviteError.set(err?.error?.detail ?? 'Failed to invite.'),
    });
  }

  changeColor(board: Board, color: string): void {
    this.api.patch(board.id, { color }).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: updated => this.boards.update(list => list.map(b => b.id === updated.id ? updated : b)),
      error: () => this.toast.show('Failed to change color.', 'error'),
    });
  }

  removeMember(userId: number): void {
    this.pendingRemoveMemberId.set(userId);
  }

  confirmRemoveMember(): void {
    const userId = this.pendingRemoveMemberId();
    const board = this.managingBoard();
    if (!board || userId === null) return;
    this.pendingRemoveMemberId.set(null);
    this.api.removeMember(board.id, userId).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: () => this.members.update(list => list.filter(m => m.user_id !== userId)),
      error: () => this.toast.show('Failed to remove member.', 'error'),
    });
  }

  changeRole(userId: number, role: BoardMemberRole): void {
    const board = this.managingBoard();
    if (!board) return;
    this.api.patchMemberRole(board.id, userId, role).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: updated => this.members.update(list => list.map(m => m.user_id === userId ? { ...m, role: updated.role } : m)),
      error: () => this.toast.show('Failed to change role.', 'error'),
    });
  }

  toggleFavorite(board: Board, event: Event): void {
    event.stopPropagation();
    const action = board.is_favorite ? this.api.unfavorite(board.id) : this.api.favorite(board.id);
    action.pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: () => this.boards.update(list => {
        const updated = list.map(b => b.id === board.id ? { ...b, is_favorite: !b.is_favorite } : b);
        return updated.sort((a, b) => {
          if (a.is_favorite !== b.is_favorite) return a.is_favorite ? -1 : 1;
          return a.title.localeCompare(b.title);
        });
      }),
      error: () => this.toast.show('Failed to update favorite.', 'error'),
    });
  }

  inputValue(event: Event): string {
    return (event.target as HTMLInputElement).value;
  }
}
