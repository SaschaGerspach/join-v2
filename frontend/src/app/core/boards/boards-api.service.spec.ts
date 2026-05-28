import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { BoardsApiService, Board } from './boards-api.service';
import { environment } from '../../../environments/environment';

describe('BoardsApiService', () => {
  let service: BoardsApiService;
  let httpMock: HttpTestingController;

  const base = environment.apiUrl;

  const mockBoard: Board = {
    id: 1, title: 'Test', color: '#000', created_by: 1,
    created_at: '2026-01-01', is_owner: true, is_favorite: false,
    is_member: true, team_id: null, team_name: null,
  };

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(BoardsApiService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => httpMock.verify());

  it('should fetch all boards', () => {
    service.getAll().subscribe(boards => {
      expect(boards).toEqual([mockBoard]);
    });
    const req = httpMock.expectOne(`${base}/boards/`);
    expect(req.request.method).toBe('GET');
    req.flush({ results: [mockBoard] });
  });

  it('should fetch a board by id', () => {
    service.getById(1).subscribe(board => expect(board.title).toBe('Test'));
    const req = httpMock.expectOne(`${base}/boards/1/`);
    expect(req.request.method).toBe('GET');
    req.flush(mockBoard);
  });

  it('should create a board', () => {
    service.create('New Board', 'kanban').subscribe(board => expect(board.id).toBe(2));
    const req = httpMock.expectOne(`${base}/boards/`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ title: 'New Board', template: 'kanban' });
    req.flush({ ...mockBoard, id: 2, title: 'New Board' });
  });

  it('should patch a board', () => {
    service.patch(1, { title: 'Updated' }).subscribe();
    const req = httpMock.expectOne(`${base}/boards/1/`);
    expect(req.request.method).toBe('PATCH');
    expect(req.request.body).toEqual({ title: 'Updated' });
    req.flush(mockBoard);
  });

  it('should delete a board', () => {
    service.delete(1).subscribe();
    const req = httpMock.expectOne(`${base}/boards/1/`);
    expect(req.request.method).toBe('DELETE');
    req.flush(null);
  });

  it('should favorite a board', () => {
    service.favorite(1).subscribe();
    const req = httpMock.expectOne(`${base}/boards/1/favorite/`);
    expect(req.request.method).toBe('POST');
    req.flush(null);
  });

  it('should unfavorite a board', () => {
    service.unfavorite(1).subscribe();
    const req = httpMock.expectOne(`${base}/boards/1/favorite/`);
    expect(req.request.method).toBe('DELETE');
    req.flush(null);
  });

  it('should invite a member', () => {
    service.inviteMember(1, 'a@b.com').subscribe();
    const req = httpMock.expectOne(`${base}/boards/1/members/`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ email: 'a@b.com' });
    req.flush({});
  });

  it('should export CSV as blob', () => {
    service.exportCsv(1).subscribe(blob => expect(blob).toBeTruthy());
    const req = httpMock.expectOne(`${base}/boards/1/export/csv/`);
    expect(req.request.responseType).toBe('blob');
    req.flush(new Blob(['csv']));
  });
});
