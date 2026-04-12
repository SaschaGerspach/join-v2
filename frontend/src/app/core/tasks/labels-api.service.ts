import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export type Label = {
  id: number;
  name: string;
  color: string;
};

@Injectable({ providedIn: 'root' })
export class LabelsApiService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = environment.apiUrl;

  getByBoard(boardId: number): Observable<Label[]> {
    return this.http.get<Label[]>(`${this.baseUrl}/boards/${boardId}/labels/`, { withCredentials: true });
  }

  create(boardId: number, name: string, color: string): Observable<Label> {
    return this.http.post<Label>(`${this.baseUrl}/boards/${boardId}/labels/`, { name, color }, { withCredentials: true });
  }

  delete(boardId: number, labelId: number): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/boards/${boardId}/labels/${labelId}/`, { withCredentials: true });
  }
}
