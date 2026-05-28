import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TasksApiService, Task } from './tasks-api.service';
import { environment } from '../../../environments/environment';

describe('TasksApiService', () => {
  let service: TasksApiService;
  let httpMock: HttpTestingController;

  const base = environment.apiUrl;

  const mockTask: Task = {
    id: 1, board: 1, column: 1, title: 'Test', description: '',
    priority: 'medium', assigned_to: [], start_date: null, due_date: null,
    recurrence: null, cover_image_url: '', order: 0, created_at: '2026-01-01',
    subtask_count: 0, subtask_done_count: 0, attachment_count: 0,
    labels: [], dependencies: [],
  };

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(TasksApiService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => httpMock.verify());

  it('should fetch tasks by board', () => {
    service.getByBoard(1).subscribe(tasks => expect(tasks.length).toBe(1));
    const req = httpMock.expectOne(r => r.url === `${base}/tasks/` && r.params.get('board') === '1');
    expect(req.request.method).toBe('GET');
    req.flush([mockTask]);
  });

  it('should create a task', () => {
    service.create(1, { title: 'New' }).subscribe(t => expect(t.title).toBe('New'));
    const req = httpMock.expectOne(`${base}/tasks/?board=1`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ title: 'New' });
    req.flush({ ...mockTask, title: 'New' });
  });

  it('should patch a task', () => {
    service.patch(1, { title: 'Updated' }).subscribe();
    const req = httpMock.expectOne(`${base}/tasks/1/`);
    expect(req.request.method).toBe('PATCH');
    req.flush(mockTask);
  });

  it('should delete a task', () => {
    service.delete(1).subscribe();
    const req = httpMock.expectOne(`${base}/tasks/1/`);
    expect(req.request.method).toBe('DELETE');
    req.flush(null);
  });

  it('should duplicate a task', () => {
    service.duplicate(1).subscribe(t => expect(t.id).toBe(2));
    const req = httpMock.expectOne(`${base}/tasks/1/duplicate/`);
    expect(req.request.method).toBe('POST');
    req.flush({ ...mockTask, id: 2 });
  });

  it('should reorder tasks', () => {
    const items = [{ id: 1, order: 0, column: 1 }];
    service.reorder(items).subscribe();
    const req = httpMock.expectOne(`${base}/tasks/reorder/`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual(items);
    req.flush(null);
  });

  it('should fetch my tasks', () => {
    service.getMyTasks().subscribe(tasks => expect(tasks).toEqual([mockTask]));
    const req = httpMock.expectOne(`${base}/tasks/my/`);
    req.flush([mockTask]);
  });

  it('should search tasks', () => {
    service.searchTasks('test').subscribe();
    const req = httpMock.expectOne(r => r.url === `${base}/tasks/my/` && r.params.get('search') === 'test');
    req.flush([]);
  });

  it('should log time', () => {
    service.logTime(1, 30, 'note').subscribe();
    const req = httpMock.expectOne(`${base}/tasks/1/time/`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ duration_minutes: 30, note: 'note' });
    req.flush({});
  });

  it('should restore an archived task', () => {
    service.restore(1).subscribe();
    const req = httpMock.expectOne(`${base}/tasks/1/restore/`);
    expect(req.request.method).toBe('POST');
    req.flush(mockTask);
  });
});
