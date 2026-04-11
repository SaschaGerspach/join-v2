import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export type Column = {
  id: number;
  board: number;
  title: string;
  order: number;
};

@Injectable({ providedIn: 'root' })
export class ColumnsApiService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = 'http://localhost:8000';

  getByBoard(boardId: number): Observable<Column[]> {
    return this.http.get<Column[]>(`${this.baseUrl}/columns/`, {
      params: { board: boardId },
      withCredentials: true,
    });
  }

  create(boardId: number, title: string): Observable<Column> {
    return this.http.post<Column>(
      `${this.baseUrl}/columns/?board=${boardId}`,
      { title },
      { withCredentials: true }
    );
  }

  delete(id: number): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/columns/${id}/`, { withCredentials: true });
  }
}
