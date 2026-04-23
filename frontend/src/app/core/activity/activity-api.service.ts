import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { environment } from '../../../environments/environment';

export type ActivityEntry = {
  id: number;
  user_name: string;
  action: 'created' | 'updated' | 'deleted' | 'moved';
  entity_type: 'task' | 'column' | 'comment';
  entity_title: string;
  details: string;
  created_at: string;
};

@Injectable({ providedIn: 'root' })
export class ActivityApiService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = environment.apiUrl;

  getByBoard(boardId: number): Observable<ActivityEntry[]> {
    return this.http.get<{ results: ActivityEntry[]; has_more: boolean }>(`${this.baseUrl}/activity/`, {
      params: { board: boardId },
      withCredentials: true,
    }).pipe(map(res => res.results));
  }
}
