import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export type AppNotification = {
  id: number;
  type: 'assignment' | 'comment' | 'mention';
  message: string;
  board_id: number | null;
  task_id: number | null;
  is_read: boolean;
  created_at: string;
};

@Injectable({ providedIn: 'root' })
export class NotificationsApiService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = environment.apiUrl;

  getAll(): Observable<AppNotification[]> {
    return this.http.get<AppNotification[]>(`${this.baseUrl}/notifications/`, { withCredentials: true });
  }

  markAsRead(id: number): Observable<AppNotification> {
    return this.http.patch<AppNotification>(`${this.baseUrl}/notifications/${id}/read/`, {}, { withCredentials: true });
  }

  markAllAsRead(): Observable<void> {
    return this.http.post<void>(`${this.baseUrl}/notifications/read-all/`, {}, { withCredentials: true });
  }
}
