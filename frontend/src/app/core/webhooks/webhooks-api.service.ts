import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export type Webhook = {
  id: number;
  url: string;
  secret: string;
  events: string[];
  is_active: boolean;
  created_at: string;
};

export type WebhookDelivery = {
  id: number;
  event_type: string;
  payload: unknown;
  response_status: number | null;
  status: 'success' | 'failed' | 'pending';
  attempted_at: string;
  delivery_id: string;
};

@Injectable({ providedIn: 'root' })
export class WebhooksApiService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = environment.apiUrl;

  getByBoard(boardId: number): Observable<Webhook[]> {
    return this.http.get<Webhook[]>(`${this.baseUrl}/webhooks/`, {
      params: { board: boardId },
      withCredentials: true,
    });
  }

  create(boardId: number, payload: { url: string; secret?: string; events: string[] }): Observable<Webhook> {
    return this.http.post<Webhook>(
      `${this.baseUrl}/webhooks/?board=${boardId}`,
      payload,
      { withCredentials: true },
    );
  }

  update(id: number, payload: Partial<Pick<Webhook, 'url' | 'secret' | 'events' | 'is_active'>>): Observable<Webhook> {
    return this.http.patch<Webhook>(`${this.baseUrl}/webhooks/${id}/`, payload, { withCredentials: true });
  }

  delete(id: number): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/webhooks/${id}/`, { withCredentials: true });
  }

  getDeliveries(webhookId: number): Observable<WebhookDelivery[]> {
    return this.http.get<WebhookDelivery[]>(`${this.baseUrl}/webhooks/${webhookId}/deliveries/`, { withCredentials: true });
  }

  getAvailableEvents(): Observable<string[]> {
    return this.http.get<string[]>(`${this.baseUrl}/webhooks/events/`, { withCredentials: true });
  }
}
