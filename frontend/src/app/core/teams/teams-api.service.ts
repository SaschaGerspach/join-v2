import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export type Team = {
  id: number;
  name: string;
  created_by: number;
  is_owner: boolean;
  member_count: number;
  created_at: string;
};

export type TeamMember = {
  user_id: number;
  email: string;
  first_name: string;
  last_name: string;
  role: string;
  avatar_url: string | null;
};

@Injectable({ providedIn: 'root' })
export class TeamsApiService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = environment.apiUrl;

  getAll(): Observable<Team[]> {
    return this.http.get<Team[]>(`${this.baseUrl}/teams/`, { withCredentials: true });
  }

  create(name: string): Observable<Team> {
    return this.http.post<Team>(`${this.baseUrl}/teams/`, { name }, { withCredentials: true });
  }

  patch(id: number, name: string): Observable<Team> {
    return this.http.patch<Team>(`${this.baseUrl}/teams/${id}/`, { name }, { withCredentials: true });
  }

  delete(id: number): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/teams/${id}/`, { withCredentials: true });
  }

  getMembers(teamId: number): Observable<TeamMember[]> {
    return this.http.get<TeamMember[]>(`${this.baseUrl}/teams/${teamId}/members/`, { withCredentials: true });
  }

  inviteMember(teamId: number, email: string): Observable<TeamMember> {
    return this.http.post<TeamMember>(`${this.baseUrl}/teams/${teamId}/members/`, { email }, { withCredentials: true });
  }

  removeMember(teamId: number, userId: number): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/teams/${teamId}/members/${userId}/`, { withCredentials: true });
  }

  patchMemberRole(teamId: number, userId: number, role: string): Observable<TeamMember> {
    return this.http.patch<TeamMember>(`${this.baseUrl}/teams/${teamId}/members/${userId}/`, { role }, { withCredentials: true });
  }
}
