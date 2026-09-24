import { TestBed } from '@angular/core/testing';
import { HttpClient, provideHttpClient, withInterceptors } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { Router } from '@angular/router';
import { throwError } from 'rxjs';
import { AuthService } from '../auth/auth.service';
import { environment } from '../../../environments/environment';
import { authInterceptor } from './auth.interceptor';

describe('authInterceptor', () => {
  let http: HttpClient;
  let httpMock: HttpTestingController;
  let routerSpy: jasmine.SpyObj<Router>;
  let authSpy: jasmine.SpyObj<AuthService>;

  beforeEach(() => {
    routerSpy = jasmine.createSpyObj('Router', ['navigate']);
    authSpy = jasmine.createSpyObj('AuthService', ['getAccessToken', 'refreshAccessToken']);
    authSpy.getAccessToken.and.returnValue(null);
    authSpy.refreshAccessToken.and.returnValue(throwError(() => new Error('refresh failed')));

    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(withInterceptors([authInterceptor])),
        provideHttpClientTesting(),
        { provide: Router, useValue: routerSpy },
        { provide: AuthService, useValue: authSpy },
      ],
    });
    http = TestBed.inject(HttpClient);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => httpMock.verify());

  it('should redirect to login when a refresh fails for a regular request', () => {
    const url = `${environment.apiUrl}/boards/`;
    http.get(url).subscribe({ error: () => {} });
    httpMock.expectOne(url).flush('unauth', { status: 401, statusText: 'Unauthorized' });
    expect(routerSpy.navigate).toHaveBeenCalledWith(['/login']);
  });

  it('should attach the token to API requests', () => {
    authSpy.getAccessToken.and.returnValue('secret-token');
    const url = `${environment.apiUrl}/boards/`;
    http.get(url).subscribe();
    const req = httpMock.expectOne(url);
    expect(req.request.headers.get('Authorization')).toBe('Bearer secret-token');
    req.flush([]);
  });

  it('should not attach the token to hosts that merely share the API url prefix', () => {
    authSpy.getAccessToken.and.returnValue('secret-token');
    const url = `${environment.apiUrl}.evil.com/collect/`;
    http.get(url).subscribe();
    const req = httpMock.expectOne(url);
    expect(req.request.headers.has('Authorization')).toBeFalse();
    req.flush({});
  });

  it('should not redirect when the startup session probe fails', () => {
    const url = `${environment.apiUrl}/auth/me/`;
    http.get(url).subscribe({ error: () => {} });
    httpMock.expectOne(url).flush('unauth', { status: 401, statusText: 'Unauthorized' });
    expect(routerSpy.navigate).not.toHaveBeenCalled();
  });
});
