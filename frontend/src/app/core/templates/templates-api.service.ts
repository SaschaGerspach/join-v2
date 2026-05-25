import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { Task } from '../tasks/tasks-api.service';

export type TaskTemplate = {
  id: number;
  name: string;
  title: string;
  description: string;
  priority: string;
  subtasks: string[];
  label_ids: number[];
  created_at: string;
};

@Injectable({ providedIn: 'root' })
export class TemplatesApiService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = environment.apiUrl;

  getByBoard(boardId: number): Observable<TaskTemplate[]> {
    return this.http.get<TaskTemplate[]>(`${this.baseUrl}/tasks/templates/`, {
      params: { board: boardId },
      withCredentials: true,
    });
  }

  create(boardId: number, payload: Omit<TaskTemplate, 'id' | 'created_at'>): Observable<TaskTemplate> {
    return this.http.post<TaskTemplate>(
      `${this.baseUrl}/tasks/templates/?board=${boardId}`,
      payload,
      { withCredentials: true },
    );
  }

  update(id: number, payload: Partial<Omit<TaskTemplate, 'id' | 'created_at'>>): Observable<TaskTemplate> {
    return this.http.patch<TaskTemplate>(`${this.baseUrl}/tasks/templates/${id}/`, payload, { withCredentials: true });
  }

  delete(id: number): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/tasks/templates/${id}/`, { withCredentials: true });
  }

  createTask(templateId: number): Observable<Task> {
    return this.http.post<Task>(`${this.baseUrl}/tasks/templates/${templateId}/create-task/`, {}, { withCredentials: true });
  }
}
