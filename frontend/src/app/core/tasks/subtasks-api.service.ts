import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export type Subtask = {
  id: number;
  task: number;
  title: string;
  done: boolean;
};

@Injectable({ providedIn: 'root' })
export class SubtasksApiService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = 'http://localhost:8000';

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
}
