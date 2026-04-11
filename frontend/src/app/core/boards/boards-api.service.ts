import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export type Board = {
  id: number;
  title: string;
  created_by: number;
  created_at: string;
};

@Injectable({ providedIn: 'root' })
export class BoardsApiService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = 'http://localhost:8000';

  getAll(): Observable<Board[]> {
    return this.http.get<Board[]>(`${this.baseUrl}/boards/`, { withCredentials: true });
  }

  create(title: string): Observable<Board> {
    return this.http.post<Board>(`${this.baseUrl}/boards/`, { title }, { withCredentials: true });
  }

  delete(id: number): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/boards/${id}/`, { withCredentials: true });
  }
}
