import { Component, inject, signal, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { BoardsApiService, Board } from '../../../../core/boards/boards-api.service';
import { LoadingSpinnerComponent } from '../../../../shared/components/loading-spinner/loading-spinner.component';
import { ConfirmDialogComponent } from '../../../../shared/components/confirm-dialog/confirm-dialog.component';

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

  boards = signal<Board[]>([]);
  newTitle = '';
  showForm = signal(false);
  loading = signal(true);
  error = signal('');
  pendingDeleteId = signal<number | null>(null);

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

    this.api.create(title).subscribe(board => {
      this.boards.update(b => [...b, board]);
      this.newTitle = '';
      this.showForm.set(false);
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
    this.api.delete(id).subscribe(() => {
      this.boards.update(b => b.filter(board => board.id !== id));
      this.pendingDeleteId.set(null);
    });
  }
}
