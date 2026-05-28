import { TestBed } from '@angular/core/testing';
import { HttpErrorResponse, HttpRequest, HttpResponse, provideHttpClient, withInterceptors } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { HttpClient } from '@angular/common/http';
import { TranslateService } from '@ngx-translate/core';
import { ToastService } from '../../shared/services/toast.service';
import { errorInterceptor } from './error.interceptor';

describe('errorInterceptor', () => {
  let http: HttpClient;
  let httpMock: HttpTestingController;
  let toastSpy: jasmine.SpyObj<ToastService>;
  let translateSpy: jasmine.SpyObj<TranslateService>;

  beforeEach(() => {
    toastSpy = jasmine.createSpyObj('ToastService', ['show']);
    translateSpy = jasmine.createSpyObj('TranslateService', ['instant']);
    translateSpy.instant.and.callFake((key: string) => key);

    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(withInterceptors([errorInterceptor])),
        provideHttpClientTesting(),
        { provide: ToastService, useValue: toastSpy },
        { provide: TranslateService, useValue: translateSpy },
      ],
    });
    http = TestBed.inject(HttpClient);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => httpMock.verify());

  it('should show server error toast on 500', () => {
    http.get('/api/test').subscribe({ error: () => {} });
    httpMock.expectOne('/api/test').flush('error', { status: 500, statusText: 'Server Error' });
    expect(toastSpy.show).toHaveBeenCalledWith('TOAST.SERVER_ERROR', 'error');
  });

  it('should show permission error toast on 403', () => {
    http.get('/api/test').subscribe({ error: () => {} });
    httpMock.expectOne('/api/test').flush('forbidden', { status: 403, statusText: 'Forbidden' });
    expect(toastSpy.show).toHaveBeenCalledWith('TOAST.PERMISSION_ERROR', 'error');
  });

  it('should show detail from 400 response', () => {
    http.get('/api/test').subscribe({ error: () => {} });
    httpMock.expectOne('/api/test').flush({ detail: 'Bad input' }, { status: 400, statusText: 'Bad Request' });
    expect(toastSpy.show).toHaveBeenCalledWith('Bad input', 'error');
  });

  it('should not toast on 401 (handled by auth interceptor)', () => {
    http.get('/api/test').subscribe({ error: () => {} });
    httpMock.expectOne('/api/test').flush('unauth', { status: 401, statusText: 'Unauthorized' });
    expect(toastSpy.show).not.toHaveBeenCalled();
  });

  it('should show network error toast on status 0', () => {
    http.get('/api/test').subscribe({ error: () => {} });
    httpMock.expectOne('/api/test').error(new ProgressEvent('error'), { status: 0 });
    expect(toastSpy.show).toHaveBeenCalledWith('TOAST.NETWORK_ERROR', 'error');
  });
});
