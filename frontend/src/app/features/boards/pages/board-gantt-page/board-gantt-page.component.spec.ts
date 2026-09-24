import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute, provideRouter } from '@angular/router';
import { TranslateModule } from '@ngx-translate/core';
import { of } from 'rxjs';
import { BoardsApiService } from '../../../../core/boards/boards-api.service';
import { ColumnsApiService } from '../../../../core/columns/columns-api.service';
import { TasksApiService } from '../../../../core/tasks/tasks-api.service';
import { ToastService } from '../../../../shared/services/toast.service';
import { BoardGanttPageComponent } from './board-gantt-page.component';

describe('BoardGanttPageComponent', () => {
  let fixture: ComponentFixture<BoardGanttPageComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [BoardGanttPageComponent, TranslateModule.forRoot()],
      providers: [
        provideRouter([]),
        { provide: ActivatedRoute, useValue: { snapshot: { paramMap: new Map([['id', '1']]) } } },
        { provide: BoardsApiService, useValue: { getById: () => of({ title: 'Board' }) } },
        { provide: TasksApiService, useValue: { getByBoard: () => of([]) } },
        { provide: ColumnsApiService, useValue: { getByBoard: () => of([]) } },
        { provide: ToastService, useValue: jasmine.createSpyObj('ToastService', ['show']) },
      ],
    });
    fixture = TestBed.createComponent(BoardGanttPageComponent);
    fixture.detectChanges();
  });

  function startDrag(): void {
    const timelineBody = document.createElement('div');
    timelineBody.className = 'timeline-body';
    fixture.nativeElement.appendChild(timelineBody);
    const event = new MouseEvent('mousedown');
    fixture.componentInstance.onDragHandleDown(event, 1);
  }

  it('should track the drag line while the mouse moves', () => {
    startDrag();
    document.dispatchEvent(new MouseEvent('mousemove', { clientX: 50, clientY: 20 }));
    expect(fixture.componentInstance.dragLineEnd()).not.toBeNull();
    document.dispatchEvent(new MouseEvent('mouseup'));
    expect(fixture.componentInstance.dragFromTaskId()).toBeNull();
  });

  it('should remove document listeners when destroyed mid-drag', () => {
    const component = fixture.componentInstance;
    startDrag();
    fixture.destroy();
    document.dispatchEvent(new MouseEvent('mousemove', { clientX: 50, clientY: 20 }));
    expect(component.dragLineEnd()).toBeNull();
  });
});
