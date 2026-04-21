import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { environment } from '../../../environments/environment';
import { CustomField } from '../tasks/tasks-api.service';

export type Board = {
  id: number;
  title: string;
  color: string;
  created_by: number;
  created_at: string;
  is_owner: boolean;
  is_favorite: boolean;
};

export type BoardMemberRole = 'admin' | 'editor' | 'viewer';

export type BoardMember = {
  user_id: number;
  email: string;
  first_name: string;
  last_name: string;
  role: BoardMemberRole;
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

  patchMemberRole(boardId: number, userId: number, role: BoardMemberRole): Observable<BoardMember> {
    return this.http.patch<BoardMember>(`${this.baseUrl}/boards/${boardId}/members/${userId}/`, { role }, { withCredentials: true });
  }

  favorite(boardId: number): Observable<void> {
    return this.http.post<void>(`${this.baseUrl}/boards/${boardId}/favorite/`, {}, { withCredentials: true });
  }

  unfavorite(boardId: number): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/boards/${boardId}/favorite/`, { withCredentials: true });
  }

  exportCsvUrl(boardId: number): string {
    return `${this.baseUrl}/boards/${boardId}/export/csv/`;
  }

  importCsv(boardId: number, file: File): Observable<{ imported: number }> {
    const form = new FormData();
    form.append('file', file);
    return this.http.post<{ imported: number }>(`${this.baseUrl}/boards/${boardId}/import/csv/`, form, { withCredentials: true });
  }

  getCustomFields(boardId: number): Observable<CustomField[]> {
    return this.http.get<CustomField[]>(`${this.baseUrl}/boards/${boardId}/fields/`, { withCredentials: true });
  }

  createCustomField(boardId: number, payload: { name: string; field_type: string; options?: string[] }): Observable<CustomField> {
    return this.http.post<CustomField>(`${this.baseUrl}/boards/${boardId}/fields/`, payload, { withCredentials: true });
  }

  deleteCustomField(boardId: number, fieldId: number): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/boards/${boardId}/fields/${fieldId}/`, { withCredentials: true });
  }
}
