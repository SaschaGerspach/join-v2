import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { EMPTY, Observable } from 'rxjs';
import { expand, reduce } from 'rxjs/operators';
import { environment } from '../../../environments/environment';

export type Contact = {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
  phone: string;
};

type ContactPage = { next: string | null; results: Contact[] };

// Matches max_page_size of the contacts endpoint.
const CONTACTS_PAGE_SIZE = 500;

@Injectable({ providedIn: 'root' })
export class ContactsApiService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = environment.apiUrl;

  // Contacts are a personal address book, so fetching every page stays cheap
  // (~150 bytes per contact); callers need the full list to resolve assignees.
  // Pages are requested by number instead of following the absolute `next` URL,
  // which may carry the wrong scheme behind the reverse proxy.
  getAll(): Observable<Contact[]> {
    const fetchPage = (page: number) => this.http.get<ContactPage>(`${this.baseUrl}/contacts/`, {
      params: { page, page_size: CONTACTS_PAGE_SIZE },
      withCredentials: true,
    });
    return fetchPage(1).pipe(
      expand((res, index) => res.next ? fetchPage(index + 2) : EMPTY),
      reduce((all, res) => all.concat(res.results), [] as Contact[]),
    );
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
