import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export type Task = {
  id: number;
  board: number;
  column: number | null;
  title: string;
  description: string;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  assigned_to: number | null;
  due_date: string | null;
  created_at: string;
  subtask_count: number;
  subtask_done_count: number;
};

export type CreateTaskPayload = {
  title: string;
  description?: string;
  priority?: string;
  column?: number | null;
  due_date?: string | null;
};

@Injectable({ providedIn: 'root' })
export class TasksApiService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = environment.apiUrl;

  getByBoard(boardId: number): Observable<Task[]> {
    return this.http.get<Task[]>(`${this.baseUrl}/tasks/`, {
      params: { board: boardId },
      withCredentials: true,
    });
  }

  create(boardId: number, payload: CreateTaskPayload): Observable<Task> {
    return this.http.post<Task>(
      `${this.baseUrl}/tasks/?board=${boardId}`,
      payload,
      { withCredentials: true }
    );
  }

  patch(id: number, payload: Partial<CreateTaskPayload>): Observable<Task> {
    return this.http.patch<Task>(`${this.baseUrl}/tasks/${id}/`, payload, { withCredentials: true });
  }

  delete(id: number): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/tasks/${id}/`, { withCredentials: true });
  }
}
