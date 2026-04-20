import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export type Recurrence = 'daily' | 'weekly' | 'biweekly' | 'monthly' | null;

export type TaskDependency = {
  id: number;
  depends_on: number;
  title: string;
};

export type CustomField = {
  id: number;
  name: string;
  field_type: 'text' | 'number' | 'date' | 'select';
  options: string[];
  order: number;
};

export type TaskFieldValue = {
  field_id: number;
  value: string;
};

export type Task = {
  id: number;
  board: number;
  column: number | null;
  title: string;
  description: string;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  assigned_to: number[];
  due_date: string | null;
  recurrence: Recurrence;
  order: number;
  created_at: string;
  subtask_count: number;
  subtask_done_count: number;
  attachment_count: number;
  labels: { id: number; name: string; color: string }[];
  dependencies: TaskDependency[];
};

export type CreateTaskPayload = {
  title: string;
  description?: string;
  priority?: string;
  column?: number | null;
  due_date?: string | null;
  recurrence?: Recurrence;
  assigned_to?: number[];
};

export type UpdateTaskPayload = Partial<CreateTaskPayload> & {
  order?: number;
  label_ids?: number[];
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

  patch(id: number, payload: UpdateTaskPayload): Observable<Task> {
    return this.http.patch<Task>(`${this.baseUrl}/tasks/${id}/`, payload, { withCredentials: true });
  }

  delete(id: number): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/tasks/${id}/`, { withCredentials: true });
  }

  reorder(items: { id: number; order: number; column: number | null }[]): Observable<void> {
    return this.http.post<void>(`${this.baseUrl}/tasks/reorder/`, items, { withCredentials: true });
  }

  getMyTasks(): Observable<Task[]> {
    return this.http.get<Task[]>(`${this.baseUrl}/tasks/my/`, { withCredentials: true });
  }

  getArchive(boardId: number): Observable<Task[]> {
    return this.http.get<Task[]>(`${this.baseUrl}/tasks/archive/`, {
      params: { board: boardId },
      withCredentials: true,
    });
  }

  restore(id: number): Observable<Task> {
    return this.http.post<Task>(`${this.baseUrl}/tasks/${id}/restore/`, {}, { withCredentials: true });
  }

  getDependencies(taskId: number): Observable<TaskDependency[]> {
    return this.http.get<TaskDependency[]>(`${this.baseUrl}/tasks/${taskId}/dependencies/`, { withCredentials: true });
  }

  addDependency(taskId: number, dependsOnId: number): Observable<TaskDependency> {
    return this.http.post<TaskDependency>(`${this.baseUrl}/tasks/${taskId}/dependencies/`, { depends_on: dependsOnId }, { withCredentials: true });
  }

  removeDependency(taskId: number, depId: number): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/tasks/${taskId}/dependencies/${depId}/`, { withCredentials: true });
  }

  getTaskFieldValues(taskId: number): Observable<{ values: TaskFieldValue[] }> {
    return this.http.get<{ values: TaskFieldValue[] }>(`${this.baseUrl}/tasks/${taskId}/fields/`, { withCredentials: true });
  }

  setTaskFieldValues(taskId: number, values: TaskFieldValue[]): Observable<{ values: TaskFieldValue[] }> {
    return this.http.put<{ values: TaskFieldValue[] }>(`${this.baseUrl}/tasks/${taskId}/fields/`, { values }, { withCredentials: true });
  }
}
