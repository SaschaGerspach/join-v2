import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { environment } from '../../../environments/environment';

export type Board = {
  id: number;
  title: string;
  created_by: number;
  created_at: string;
};

@Injectable({ providedIn: 'root' })
export class BoardsApiService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = environment.apiUrl;

  getAll(): Observable<Board[]> {
    return this.http.get<{ results: Board[] }>(`${this.baseUrl}/boards/`, { withCredentials: true }).pipe(
      map(r => r.results)
    );
  }

  getById(id: number): Observable<Board> {
    return this.http.get<Board>(`${this.baseUrl}/boards/${id}/`, { withCredentials: true });
  }

  create(title: string): Observable<Board> {
    return this.http.post<Board>(`${this.baseUrl}/boards/`, { title }, { withCredentials: true });
  }

  patch(id: number, payload: Partial<{ title: string }>): Observable<Board> {
    return this.http.patch<Board>(`${this.baseUrl}/boards/${id}/`, payload, { withCredentials: true });
  }

  delete(id: number): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/boards/${id}/`, { withCredentials: true });
  }
}
