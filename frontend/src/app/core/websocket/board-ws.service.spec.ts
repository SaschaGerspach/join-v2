import { isBoardWsEvent } from './board-ws.service';

describe('isBoardWsEvent', () => {
  const knownEvents = [
    'task_created', 'task_updated', 'task_deleted', 'tasks_reordered',
    'column_created', 'column_updated', 'column_deleted', 'columns_reordered',
    'automation_executed',
    'presence_list', 'presence_joined', 'presence_left',
  ];

  it('should accept every known event type', () => {
    for (const event of knownEvents) {
      expect(isBoardWsEvent({ event, data: {} })).withContext(event).toBe(true);
    }
  });

  it('should accept the real columns_reordered payload', () => {
    const payload = {
      event: 'columns_reordered',
      data: [{ id: 1, board: 7, title: 'To do', order: 0, wip_limit: null }],
    };
    expect(isBoardWsEvent(payload)).toBe(true);
  });

  it('should accept the real automation_executed payload', () => {
    const payload = {
      event: 'automation_executed',
      data: { rule_name: 'Auto assign', task_id: 42, actions: ['assign_user'] },
    };
    expect(isBoardWsEvent(payload)).toBe(true);
  });

  it('should reject unknown event types', () => {
    expect(isBoardWsEvent({ event: 'task_exploded', data: {} })).toBe(false);
  });

  it('should reject messages without a data field', () => {
    expect(isBoardWsEvent({ event: 'task_created' })).toBe(false);
  });

  it('should reject malformed values', () => {
    expect(isBoardWsEvent(null)).toBe(false);
    expect(isBoardWsEvent('task_created')).toBe(false);
    expect(isBoardWsEvent({ event: 5, data: {} })).toBe(false);
    expect(isBoardWsEvent({})).toBe(false);
  });
});
