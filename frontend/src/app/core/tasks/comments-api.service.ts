import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export type Comment = {
  id: number;
  task: number;
  author_id: number;
  author_name: string;
  text: string;
  created_at: string;
  updated_at: string;
};

@Injectable({ providedIn: 'root' })
export class CommentsApiService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = environment.apiUrl;

  getAll(taskId: number): Observable<Comment[]> {
    return this.http.get<Comment[]>(`${this.baseUrl}/tasks/${taskId}/comments/`, { withCredentials: true });
  }

  create(taskId: number, text: string): Observable<Comment> {
    return this.http.post<Comment>(`${this.baseUrl}/tasks/${taskId}/comments/`, { text }, { withCredentials: true });
  }

  patch(taskId: number, commentId: number, text: string): Observable<Comment> {
    return this.http.patch<Comment>(`${this.baseUrl}/tasks/${taskId}/comments/${commentId}/`, { text }, { withCredentials: true });
  }

  delete(taskId: number, commentId: number): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/tasks/${taskId}/comments/${commentId}/`, { withCredentials: true });
  }
}
