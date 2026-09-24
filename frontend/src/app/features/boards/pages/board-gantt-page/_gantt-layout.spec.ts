import { Task } from '../../../../core/tasks/tasks-api.service';
import {
  ROW_HEIGHT,
  buildDependencyLines,
  buildGanttBars,
  buildTimelineHeaders,
  computeDateRange,
  todayPosition,
} from './_gantt-layout';

function makeTask(id: number, overrides: Partial<Task> = {}): Task {
  return {
    id,
    board: 1,
    column: 10,
    title: `Task ${id}`,
    description: '',
    priority: 'medium',
    assigned_to: [],
    start_date: null,
    due_date: null,
    recurrence: null,
    cover_image_url: '',
    order: 0,
    created_at: '2026-09-01T00:00:00Z',
    subtask_count: 0,
    subtask_done_count: 0,
    attachment_count: 0,
    labels: [],
    dependencies: [],
    ...overrides,
  };
}

describe('gantt layout', () => {
  const tasks = [
    makeTask(1, { start_date: '2026-09-10', due_date: '2026-09-12', priority: 'high' }),
    makeTask(2, { due_date: '2026-09-20' }),
  ];

  it('should pad the date range by a week on both sides', () => {
    const range = computeDateRange(tasks);
    expect(range.start.getDate()).toBe(3);
    expect(range.end.getDate()).toBe(27);
    expect(range.days).toBe(25);
  });

  it('should return an empty range without dated tasks', () => {
    expect(computeDateRange([]).days).toBe(0);
    expect(buildGanttBars([], computeDateRange([]), new Map())).toEqual([]);
  });

  for (const zoom of ['day', 'week', 'month'] as const) {
    it(`should cover every day of the range with ${zoom} headers`, () => {
      const range = computeDateRange(tasks);
      const headers = buildTimelineHeaders(range.start, range.days, zoom);
      expect(headers.reduce((sum, h) => sum + h.span, 0)).toBe(range.days);
    });
  }

  it('should split week headers at the end of each week', () => {
    const start = new Date(2026, 8, 2);
    const headers = buildTimelineHeaders(start, 14, 'week');
    expect(headers[0].span).toBe(7 - start.getDay());
  });

  it('should position bars inside the timeline with priority color and column title', () => {
    const range = computeDateRange(tasks);
    const bars = buildGanttBars(tasks, range, new Map([[10, 'Doing']]));
    expect(bars.length).toBe(2);
    for (const bar of bars) {
      expect(bar.left).toBeGreaterThan(0);
      expect(bar.left + bar.width).toBeLessThan(100);
      expect(bar.columnTitle).toBe('Doing');
    }
    expect(bars[0].color).toBe('#ff3d00');
    expect(bars[1].left).toBeGreaterThan(bars[0].left);
  });

  it('should only report today inside the range', () => {
    const range = computeDateRange(tasks);
    expect(todayPosition(range, new Date(2026, 0, 1))).toBe(-1);
    const middle = todayPosition(range, new Date(2026, 8, 15, 12));
    expect(middle).toBeGreaterThan(0);
    expect(middle).toBeLessThan(100);
  });

  it('should connect dependent bars from the end of the source to the start of the target', () => {
    const dependent = makeTask(3, {
      start_date: '2026-09-14',
      due_date: '2026-09-16',
      dependencies: [
        { id: 7, depends_on: 1, title: 'Task 1' },
        { id: 8, depends_on: 999, title: 'Hidden' },
      ],
    });
    const all = [...tasks, dependent];
    const bars = buildGanttBars(all, computeDateRange(all), new Map());
    const lines = buildDependencyLines(bars, 1000);

    expect(lines.length).toBe(1);
    expect(lines[0].depId).toBe(7);
    expect(lines[0].endY).toBe(2 * ROW_HEIGHT + ROW_HEIGHT / 2);
    expect(lines[0].endX).toBeCloseTo(bars[2].left * 10);
    expect(lines[0].path.startsWith(`M ${(bars[0].left + bars[0].width) * 10} ${ROW_HEIGHT / 2}`)).toBeTrue();
  });
});
