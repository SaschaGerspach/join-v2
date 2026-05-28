import { TestBed } from '@angular/core/testing';
import { HttpClient, provideHttpClient, withInterceptors } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TranslateService } from '@ngx-translate/core';
import { ToastService } from '../../shared/services/toast.service';
import { OfflineQueueService } from '../offline/offline-queue.service';
import { offlineInterceptor } from './offline.interceptor';

describe('offlineInterceptor', () => {
  let http: HttpClient;
  let httpMock: HttpTestingController;
  let queueSpy: jasmine.SpyObj<OfflineQueueService>;
  let toastSpy: jasmine.SpyObj<ToastService>;
  let translateSpy: jasmine.SpyObj<TranslateService>;

  beforeEach(() => {
    queueSpy = jasmine.createSpyObj('OfflineQueueService', ['enqueue']);
    toastSpy = jasmine.createSpyObj('ToastService', ['show']);
    translateSpy = jasmine.createSpyObj('TranslateService', ['instant']);
    translateSpy.instant.and.callFake((key: string) => key);

    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(withInterceptors([offlineInterceptor])),
        provideHttpClientTesting(),
        { provide: OfflineQueueService, useValue: queueSpy },
        { provide: ToastService, useValue: toastSpy },
        { provide: TranslateService, useValue: translateSpy },
      ],
    });
    http = TestBed.inject(HttpClient);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => httpMock.verify());

  it('should pass through GET requests when offline', () => {
    spyOnProperty(navigator, 'onLine', 'get').and.returnValue(false);
    http.get('/api/test').subscribe();
    const req = httpMock.expectOne('/api/test');
    expect(req.request.method).toBe('GET');
    req.flush([]);
  });

  it('should pass through requests when online', () => {
    spyOnProperty(navigator, 'onLine', 'get').and.returnValue(true);
    http.post('/api/test', { data: 1 }).subscribe();
    const req = httpMock.expectOne('/api/test');
    expect(req.request.method).toBe('POST');
    req.flush({});
    expect(queueSpy.enqueue).not.toHaveBeenCalled();
  });

  it('should enqueue write requests when offline', () => {
    spyOnProperty(navigator, 'onLine', 'get').and.returnValue(false);
    http.post('/api/test', { data: 1 }).subscribe({ complete: () => {}, error: () => {} });
    expect(queueSpy.enqueue).toHaveBeenCalledWith('POST', '/api/test', { data: 1 });
    expect(toastSpy.show).toHaveBeenCalledWith('TOAST.OFFLINE_CHANGE_QUEUED');
    httpMock.expectNone('/api/test');
  });
});
