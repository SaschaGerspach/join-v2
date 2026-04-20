import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { environment } from '../../../environments/environment';

export type Board = {
  id: number;
  title: string;
  color: string;
  created_by: number;
  created_at: string;
  is_owner: boolean;
  is_favorite: boolean;
};

export type BoardMember = {
  user_id: number;
  email: string;
  first_name: string;
  last_name: string;
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

  create(title: string, template: string = 'kanban'): Observable<Board> {
    return this.http.post<Board>(`${this.baseUrl}/boards/`, { title, template }, { withCredentials: true });
  }

  patch(id: number, payload: Partial<{ title: string; color: string }>): Observable<Board> {
    return this.http.patch<Board>(`${this.baseUrl}/boards/${id}/`, payload, { withCredentials: true });
  }

  delete(id: number): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/boards/${id}/`, { withCredentials: true });
  }

  getMembers(boardId: number): Observable<BoardMember[]> {
    return this.http.get<BoardMember[]>(`${this.baseUrl}/boards/${boardId}/members/`, { withCredentials: true });
  }

  inviteMember(boardId: number, email: string): Observable<BoardMember> {
    return this.http.post<BoardMember>(`${this.baseUrl}/boards/${boardId}/members/`, { email }, { withCredentials: true });
  }

  removeMember(boardId: number, userId: number): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/boards/${boardId}/members/${userId}/`, { withCredentials: true });
  }

  favorite(boardId: number): Observable<void> {
    return this.http.post<void>(`${this.baseUrl}/boards/${boardId}/favorite/`, {}, { withCredentials: true });
  }

  unfavorite(boardId: number): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/boards/${boardId}/favorite/`, { withCredentials: true });
  }
}
