import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export type Subtask = {
  id: number;
  task: number;
  title: string;
  done: boolean;
  order: number;
};

@Injectable({ providedIn: 'root' })
export class SubtasksApiService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = environment.apiUrl;

  getByTask(taskId: number): Observable<Subtask[]> {
    return this.http.get<Subtask[]>(`${this.baseUrl}/tasks/${taskId}/subtasks/`, { withCredentials: true });
  }

  create(taskId: number, title: string): Observable<Subtask> {
    return this.http.post<Subtask>(`${this.baseUrl}/tasks/${taskId}/subtasks/`, { title }, { withCredentials: true });
  }

  patch(taskId: number, subtaskId: number, payload: Partial<{ title: string; done: boolean }>): Observable<Subtask> {
    return this.http.patch<Subtask>(
      `${this.baseUrl}/tasks/${taskId}/subtasks/${subtaskId}/`,
      payload,
      { withCredentials: true }
    );
  }

  delete(taskId: number, subtaskId: number): Observable<void> {
    return this.http.delete<void>(
      `${this.baseUrl}/tasks/${taskId}/subtasks/${subtaskId}/`,
      { withCredentials: true }
    );
  }

  reorder(taskId: number, ids: number[]): Observable<void> {
    return this.http.post<void>(
      `${this.baseUrl}/tasks/${taskId}/subtasks/reorder/`,
      { ids },
      { withCredentials: true }
    );
  }
}
