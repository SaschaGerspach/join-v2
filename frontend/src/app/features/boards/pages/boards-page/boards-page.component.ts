import { ChangeDetectionStrategy, Component, DestroyRef, inject, signal, OnInit } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { BoardsApiService, Board, BoardMember } from '../../../../core/boards/boards-api.service';
import { LoadingSpinnerComponent } from '../../../../shared/components/loading-spinner/loading-spinner.component';
import { ConfirmDialogComponent } from '../../../../shared/components/confirm-dialog/confirm-dialog.component';
import { ToastService } from '../../../../shared/services/toast.service';

@Component({
  selector: 'app-boards-page',
  standalone: true,
  imports: [FormsModule, LoadingSpinnerComponent, ConfirmDialogComponent],
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
  newTitle = '';
  newTemplate = 'kanban';
  showForm = signal(false);
  loading = signal(true);
  pendingDeleteId = signal<number | null>(null);

  managingBoard = signal<Board | null>(null);
  members = signal<BoardMember[]>([]);
  inviteEmail = '';
  inviteError = signal('');

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
    const board = this.managingBoard();
    if (!board) return;
    this.api.removeMember(board.id, userId).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: () => this.members.update(list => list.filter(m => m.user_id !== userId)),
      error: () => this.toast.show('Failed to remove member.', 'error'),
    });
  }

  inputValue(event: Event): string {
    return (event.target as HTMLInputElement).value;
  }
}
