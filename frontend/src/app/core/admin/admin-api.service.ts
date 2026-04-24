import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export type Trend = {
  total: number;
  this_week: number;
  last_week: number;
};

export type WarnUser = {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
};

export type WarnGroup = {
  count: number;
  list: WarnUser[];
};

export type AdminStats = {
  users: Trend;
  boards: Trend;
  tasks: Trend;
  contacts: number;
  unverified_users: WarnGroup;
  inactive_users: WarnGroup;
  never_logged_in: WarnGroup;
};

export type AuditLogEntry = {
  id: number;
  timestamp: string;
  user_email: string | null;
  event_type: string;
  ip_address: string | null;
  detail: string;
};

export type AuditLogResponse = {
  results: AuditLogEntry[];
  event_types: string[];
};

export type TopBoard = {
  id: number;
  title: string;
  color: string;
  task_count: number;
};

export type RecentBoard = {
  id: number;
  title: string;
  color: string;
  last_activity: string;
};

export type AdminBoardsResponse = {
  active_boards: number;
  inactive_boards: number;
  top_boards: TopBoard[];
  recent_boards: RecentBoard[];
};

@Injectable({ providedIn: 'root' })
export class AdminApiService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = environment.apiUrl;

  getStats(): Observable<AdminStats> {
    return this.http.get<AdminStats>(`${this.baseUrl}/admin-api/stats/`, { withCredentials: true });
  }

  getAuditLog(eventType?: string, limit = 20): Observable<AuditLogResponse> {
    let params = new HttpParams().set('limit', limit);
    if (eventType) params = params.set('event_type', eventType);
    return this.http.get<AuditLogResponse>(`${this.baseUrl}/admin-api/audit-log/`, { params, withCredentials: true });
  }

  getBoards(): Observable<AdminBoardsResponse> {
    return this.http.get<AdminBoardsResponse>(`${this.baseUrl}/admin-api/boards/`, { withCredentials: true });
  }
}
