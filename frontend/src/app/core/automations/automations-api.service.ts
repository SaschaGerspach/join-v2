import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export type TriggerType =
  | 'task_moved_to_column'
  | 'task_created'
  | 'priority_set'
  | 'all_subtasks_done'
  | 'deadline_approaching'
  | 'label_added';

export type ConditionType = 'priority_equals' | 'label_set' | 'assignee_equals';

export type ActionType =
  | 'move_to_column'
  | 'set_priority'
  | 'assign_user'
  | 'set_label'
  | 'remove_label'
  | 'notify_creator'
  | 'notify_assignees'
  | 'notify_user';

export type RuleCondition = {
  condition_type: ConditionType;
  config: Record<string, unknown>;
};

export type RuleAction = {
  action_type: ActionType;
  config: Record<string, unknown>;
  order: number;
};

export type AutomationRule = {
  id: number;
  name: string;
  board: number | null;
  trigger_type: TriggerType;
  trigger_config: Record<string, unknown>;
  conditions: RuleCondition[];
  actions: RuleAction[];
  is_active: boolean;
  is_default: boolean;
  created_at: string;
};

export type AutomationLog = {
  id: number;
  rule_name: string;
  task_title: string;
  task_id: number;
  trigger_type: string;
  actions_executed: string[];
  executed_at: string;
};

export type CreateRulePayload = {
  name: string;
  trigger_type: TriggerType;
  trigger_config?: Record<string, unknown>;
  conditions?: RuleCondition[];
  actions: RuleAction[];
};

@Injectable({ providedIn: 'root' })
export class AutomationsApiService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = environment.apiUrl;

  getByBoard(boardId: number): Observable<AutomationRule[]> {
    return this.http.get<AutomationRule[]>(`${this.baseUrl}/boards/${boardId}/automations/`, { withCredentials: true });
  }

  create(boardId: number, payload: CreateRulePayload): Observable<AutomationRule> {
    return this.http.post<AutomationRule>(`${this.baseUrl}/boards/${boardId}/automations/`, payload, { withCredentials: true });
  }

  patch(boardId: number, ruleId: number, payload: Partial<CreateRulePayload & { is_active: boolean }>): Observable<AutomationRule> {
    return this.http.patch<AutomationRule>(`${this.baseUrl}/boards/${boardId}/automations/${ruleId}/`, payload, { withCredentials: true });
  }

  delete(boardId: number, ruleId: number): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/boards/${boardId}/automations/${ruleId}/`, { withCredentials: true });
  }

  toggle(boardId: number, ruleId: number): Observable<AutomationRule> {
    return this.http.post<AutomationRule>(`${this.baseUrl}/boards/${boardId}/automations/${ruleId}/toggle/`, {}, { withCredentials: true });
  }

  getLogs(boardId: number): Observable<AutomationLog[]> {
    return this.http.get<AutomationLog[]>(`${this.baseUrl}/boards/${boardId}/automations/logs/`, { withCredentials: true });
  }
}
