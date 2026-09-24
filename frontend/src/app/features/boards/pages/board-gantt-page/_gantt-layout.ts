import { Task } from '../../../../core/tasks/tasks-api.service';
import { PRIORITY_COLORS, BRAND_COLOR } from '../../../../shared/constants/colors';

export type ZoomLevel = 'day' | 'week' | 'month';

export type DateRange = { start: Date; end: Date; days: number };

export type GanttBar = {
  task: Task;
  left: number;
  width: number;
  color: string;
  columnTitle: string;
};

export type DependencyLine = {
  path: string;
  endX: number;
  endY: number;
  taskId: number;
  depId: number;
  dependsOnTitle: string;
};

// Must match the .timeline-row height in the stylesheet.
export const ROW_HEIGHT = 44;

export const COLUMN_WIDTH: Record<ZoomLevel, number> = { day: 40, week: 20, month: 8 };

const DAY_MS = 24 * 60 * 60 * 1000;
const RANGE_PADDING_DAYS = 7;
const MIN_BAR_WIDTH_PERCENT = 0.5;
const CURVE_OFFSET_PX = 30;

export function computeDateRange(tasks: Task[]): DateRange {
  if (tasks.length === 0) return { start: new Date(), end: new Date(), days: 0 };

  let min = Infinity;
  let max = -Infinity;
  for (const t of tasks) {
    const s = t.start_date ? new Date(t.start_date).getTime() : null;
    const d = t.due_date ? new Date(t.due_date).getTime() : null;
    const earliest = s ?? d!;
    const latest = d ?? s!;
    if (earliest < min) min = earliest;
    if (latest > max) max = latest;
  }

  const start = new Date(min);
  start.setDate(start.getDate() - RANGE_PADDING_DAYS);
  const end = new Date(max);
  end.setDate(end.getDate() + RANGE_PADDING_DAYS);
  const days = Math.ceil((end.getTime() - start.getTime()) / DAY_MS) + 1;
  return { start, end, days };
}

export function buildTimelineHeaders(start: Date, days: number, zoom: ZoomLevel): { label: string; span: number }[] {
  const headers: { label: string; span: number }[] = [];
  let i = 0;
  while (i < days) {
    const d = new Date(start);
    d.setDate(d.getDate() + i);
    let span = 1;
    if (zoom === 'week') {
      span = Math.min(7 - d.getDay() || 7, days - i);
    } else if (zoom === 'month') {
      const daysInMonth = new Date(d.getFullYear(), d.getMonth() + 1, 0).getDate();
      span = Math.min(daysInMonth - d.getDate() + 1, days - i);
    }
    headers.push({ label: formatHeaderDate(d, zoom), span });
    i += span;
  }
  return headers;
}

export function buildGanttBars(tasks: Task[], range: DateRange, columnTitles: Map<number, string>): GanttBar[] {
  if (range.days === 0) return [];
  const startMs = range.start.getTime();
  const totalMs = range.days * DAY_MS;

  return tasks.map(t => {
    const s = t.start_date ? new Date(t.start_date).getTime() : null;
    const d = t.due_date ? new Date(t.due_date + 'T23:59:59').getTime() : null;
    const barStart = s ?? d!;
    const barEnd = d ?? s! + DAY_MS;

    return {
      task: t,
      left: ((barStart - startMs) / totalMs) * 100,
      width: Math.max(((barEnd - barStart) / totalMs) * 100, MIN_BAR_WIDTH_PERCENT),
      color: PRIORITY_COLORS[t.priority] ?? BRAND_COLOR,
      columnTitle: (t.column ? columnTitles.get(t.column) : null) ?? '',
    };
  });
}

export function todayPosition(range: DateRange, now = new Date()): number {
  if (range.days === 0) return -1;
  const pos = ((now.getTime() - range.start.getTime()) / (range.days * DAY_MS)) * 100;
  return pos >= 0 && pos <= 100 ? pos : -1;
}

export function rowCenter(index: number): number {
  return index * ROW_HEIGHT + ROW_HEIGHT / 2;
}

export function buildDependencyLines(bars: GanttBar[], timelineWidth: number): DependencyLine[] {
  const barIndex = new Map<number, number>();
  bars.forEach((b, i) => barIndex.set(b.task.id, i));

  const lines: DependencyLine[] = [];
  bars.forEach((bar, targetIdx) => {
    for (const dep of bar.task.dependencies) {
      const sourceIdx = barIndex.get(dep.depends_on);
      if (sourceIdx === undefined) continue;
      const source = bars[sourceIdx];
      const x1 = (source.left + source.width) / 100 * timelineWidth;
      const y1 = rowCenter(sourceIdx);
      const x2 = bar.left / 100 * timelineWidth;
      const y2 = rowCenter(targetIdx);
      lines.push({
        path: `M ${x1} ${y1} C ${x1 + CURVE_OFFSET_PX} ${y1} ${x2 - CURVE_OFFSET_PX} ${y2} ${x2} ${y2}`,
        endX: x2,
        endY: y2,
        taskId: bar.task.id,
        depId: dep.id,
        dependsOnTitle: dep.title,
      });
    }
  });
  return lines;
}

function formatHeaderDate(d: Date, zoom: ZoomLevel): string {
  const month = d.toLocaleString(undefined, { month: 'short' });
  if (zoom === 'month') return `${month} ${d.getFullYear()}`;
  return `${d.getDate()} ${month}`;
}
