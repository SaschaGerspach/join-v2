import { Component, inject, signal, OnInit } from '@angular/core';
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
  styleUrl: './boards-page.component.scss'
})
export class BoardsPageComponent implements OnInit {
  private readonly api = inject(BoardsApiService);
  private readonly router = inject(Router);
  private readonly toast = inject(ToastService);

  boards = signal<Board[]>([]);
  newTitle = '';
  showForm = signal(false);
  loading = signal(true);
  error = signal('');
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
    this.error.set('');
    this.api.getAll().subscribe({
      next: boards => { this.boards.set(boards); this.loading.set(false); },
      error: () => { this.error.set('Failed to load boards.'); this.loading.set(false); },
    });
  }

  createBoard(): void {
    const title = this.newTitle.trim();
    if (!title) return;

    this.api.create(title).subscribe({
      next: board => {
        this.boards.update(b => [...b, board]);
        this.newTitle = '';
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
    this.api.delete(id).subscribe({
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
    this.api.getMembers(board.id).subscribe({
      next: m => this.members.set(m),
      error: () => this.members.set([]),
    });
  }

  invite(): void {
    const board = this.managingBoard();
    if (!board || !this.inviteEmail.trim()) return;
    this.inviteError.set('');
    this.api.inviteMember(board.id, this.inviteEmail.trim()).subscribe({
      next: m => { this.members.update(list => [...list, m]); this.inviteEmail = ''; this.toast.show('Invitation sent'); },
      error: (err) => this.inviteError.set(err?.error?.detail ?? 'Failed to invite.'),
    });
  }

  removeMember(userId: number): void {
    const board = this.managingBoard();
    if (!board) return;
    this.api.removeMember(board.id, userId).subscribe({
      next: () => this.members.update(list => list.filter(m => m.user_id !== userId)),
      error: () => this.toast.show('Failed to remove member.', 'error'),
    });
  }
}
