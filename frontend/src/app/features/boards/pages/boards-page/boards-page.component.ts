import { Component, inject, signal, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { BoardsApiService, Board } from '../../../../core/boards/boards-api.service';

@Component({
  selector: 'app-boards-page',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './boards-page.component.html',
  styleUrl: './boards-page.component.scss'
})
export class BoardsPageComponent implements OnInit {
  private readonly api = inject(BoardsApiService);
  private readonly router = inject(Router);

  boards = signal<Board[]>([]);
  newTitle = '';
  showForm = signal(false);

  ngOnInit(): void {
    this.loadBoards();
  }

  loadBoards(): void {
    this.api.getAll().subscribe(boards => this.boards.set(boards));
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

  deleteBoard(id: number): void {
    this.api.delete(id).subscribe(() => {
      this.boards.update(b => b.filter(board => board.id !== id));
    });
  }
}
