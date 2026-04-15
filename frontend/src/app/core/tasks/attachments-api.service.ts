import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export type Attachment = {
  id: number;
  filename: string;
  url: string;
  size: number;
  uploaded_at: string;
};

@Injectable({ providedIn: 'root' })
export class AttachmentsApiService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = environment.apiUrl;

  getByTask(taskId: number): Observable<Attachment[]> {
    return this.http.get<Attachment[]>(`${this.baseUrl}/tasks/${taskId}/attachments/`, { withCredentials: true });
  }

  upload(taskId: number, file: File): Observable<Attachment> {
    const fd = new FormData();
    fd.append('file', file);
    return this.http.post<Attachment>(`${this.baseUrl}/tasks/${taskId}/attachments/`, fd, { withCredentials: true });
  }

  delete(taskId: number, attachmentId: number): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/tasks/${taskId}/attachments/${attachmentId}/`, { withCredentials: true });
  }
}
