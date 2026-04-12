import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export type Contact = {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
  phone: string;
};

@Injectable({ providedIn: 'root' })
export class ContactsApiService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = environment.apiUrl;

  getAll(): Observable<Contact[]> {
    return this.http.get<Contact[]>(`${this.baseUrl}/contacts/`, { withCredentials: true });
  }

  create(payload: Omit<Contact, 'id'>): Observable<Contact> {
    return this.http.post<Contact>(`${this.baseUrl}/contacts/`, payload, { withCredentials: true });
  }

  patch(id: number, payload: Partial<Omit<Contact, 'id'>>): Observable<Contact> {
    return this.http.patch<Contact>(`${this.baseUrl}/contacts/${id}/`, payload, { withCredentials: true });
  }

  delete(id: number): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/contacts/${id}/`, { withCredentials: true });
  }
}
