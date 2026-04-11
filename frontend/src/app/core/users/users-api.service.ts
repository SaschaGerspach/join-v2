import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export type UserProfile = {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
};

@Injectable({ providedIn: 'root' })
export class UsersApiService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = 'http://localhost:8000';

  get(id: number): Observable<UserProfile> {
    return this.http.get<UserProfile>(`${this.baseUrl}/users/${id}/`, { withCredentials: true });
  }

  patch(id: number, payload: Partial<UserProfile & { password: string }>): Observable<UserProfile> {
    return this.http.patch<UserProfile>(`${this.baseUrl}/users/${id}/`, payload, { withCredentials: true });
  }
}
