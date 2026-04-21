import { DestroyRef, WritableSignal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { Column } from '../../../core/columns/columns-api.service';
import { Task } from '../../../core/tasks/tasks-api.service';
import { BoardWsService, PresenceUser } from '../../../core/websocket/board-ws.service';

export function connectBoardWebSocket(
  boardId: number,
  boardWs: BoardWsService,
  tasks: WritableSignal<Task[]>,
  columns: WritableSignal<Column[]>,
  onlineUsers: WritableSignal<PresenceUser[]>,
  destroyRef: DestroyRef,
): void {
  boardWs.connect(boardId);
  boardWs.events$.pipe(takeUntilDestroyed(destroyRef)).subscribe(evt => {
    switch (evt.event) {
      case 'task_created':
        tasks.update(t => t.some(x => x.id === evt.data.id) ? t : [...t, evt.data]);
        break;
      case 'task_updated':
        tasks.update(t => t.map(x => x.id === evt.data.id ? evt.data : x));
        break;
      case 'task_deleted':
        tasks.update(t => t.filter(x => x.id !== evt.data.id));
        break;
      case 'tasks_reordered':
        tasks.update(list => {
          const updated = evt.data;
          return list.map(t => updated.find(x => x.id === t.id) ?? t);
        });
        break;
      case 'column_created':
        columns.update(c => c.some(x => x.id === evt.data.id) ? c : [...c, evt.data]);
        break;
      case 'column_updated':
        columns.update(c => c.map(x => x.id === evt.data.id ? evt.data : x));
        break;
      case 'column_deleted':
        columns.update(c => c.filter(x => x.id !== evt.data.id));
        break;
      case 'presence_list':
        onlineUsers.set(evt.data);
        break;
      case 'presence_joined':
        onlineUsers.update(list => list.some(u => u.id === evt.data.id) ? list : [...list, evt.data]);
        break;
      case 'presence_left':
        onlineUsers.update(list => list.filter(u => u.id !== evt.data.id));
        break;
    }
  });
}
