import { ComponentFixture, TestBed } from '@angular/core/testing';
import { signal } from '@angular/core';
import { TranslateModule } from '@ngx-translate/core';
import { Task } from '../../../../core/tasks/tasks-api.service';
import { BoardStateService } from '../../services/board-state.service';
import { TaskCardComponent } from './task-card.component';

function makeTask(overrides: Partial<Task> = {}): Task {
  return {
    id: 7,
    board: 1,
    column: 1,
    title: 'Write tests',
    description: '',
    priority: 'high',
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

describe('TaskCardComponent', () => {
  let fixture: ComponentFixture<TaskCardComponent>;
  let el: HTMLElement;
  const state = {
    pendingDeleteTaskId: signal<number | null>(null),
    isTaskSelected: () => false,
    toggleTaskSelection: jasmine.createSpy('toggleTaskSelection'),
    priorityClass: (p: string) => `priority-${p}`,
    isOverdue: (d: string | null) => d === '2020-01-01',
    isSoon: () => false,
    contactName: (id: number) => (id === 3 ? 'Laura Mueller' : ''),
    contactInitials: (id: number) => (id === 3 ? 'LM' : ''),
  };

  function render(task: Task): void {
    fixture.componentRef.setInput('task', task);
    fixture.detectChanges();
  }

  beforeEach(() => {
    state.pendingDeleteTaskId.set(null);
    TestBed.configureTestingModule({
      imports: [TaskCardComponent, TranslateModule.forRoot()],
      providers: [{ provide: BoardStateService, useValue: state }],
    });
    fixture = TestBed.createComponent(TaskCardComponent);
    el = fixture.nativeElement;
  });

  it('should render title and priority badge', () => {
    render(makeTask());
    expect(el.querySelector('.task-title')?.textContent).toContain('Write tests');
    expect(el.querySelector('.task-priority')?.classList).toContain('priority-high');
  });

  it('should show subtask progress', () => {
    render(makeTask({ subtask_count: 4, subtask_done_count: 1 }));
    const fill = el.querySelector<HTMLElement>('.subtask-progress-fill');
    expect(fill?.style.width).toBe('25%');
    expect(el.querySelector('.subtask-progress-label')?.textContent).toContain('1/4');
  });

  it('should mark overdue due dates', () => {
    render(makeTask({ due_date: '2020-01-01' }));
    expect(el.querySelector('.task-due-date')?.classList).toContain('overdue');
  });

  it('should only show assignees with a known contact', () => {
    render(makeTask({ assigned_to: [3, 99] }));
    const avatars = el.querySelectorAll('.assignee-avatar');
    expect(avatars.length).toBe(1);
    expect(avatars[0].textContent).toContain('LM');
  });

  it('should request deletion without opening the task', () => {
    render(makeTask());
    const parentClick = jasmine.createSpy('parentClick');
    el.addEventListener('click', parentClick);
    el.querySelector<HTMLButtonElement>('.btn-delete-task')!.click();
    expect(state.pendingDeleteTaskId()).toBe(7);
    expect(parentClick).not.toHaveBeenCalled();
  });
});
