import { TestBed } from '@angular/core/testing';
import { of, throwError } from 'rxjs';
import { AuthService } from './auth.service';
import { AuthApiService } from './auth-api.service';

describe('AuthService', () => {
  let service: AuthService;
  let apiSpy: jasmine.SpyObj<AuthApiService>;

  beforeEach(() => {
    apiSpy = jasmine.createSpyObj('AuthApiService', ['me', 'login', 'logout']);
    apiSpy.logout.and.returnValue(of(void 0));

    TestBed.configureTestingModule({
      providers: [{ provide: AuthApiService, useValue: apiSpy }],
    });
    service = TestBed.inject(AuthService);
  });

  it('should not be logged in initially', () => {
    expect(service.isLoggedIn()).toBeFalse();
    expect(service.user()).toBeNull();
  });

  it('should set user after successful init', () => {
    const user = { id: 1, email: 'a@b.com', first_name: 'A', last_name: 'B', is_staff: false, totp_enabled: false, avatar_url: null };
    apiSpy.me.and.returnValue(of(user));
    service.init();
    expect(service.user()).toEqual(user);
    expect(service.isLoggedIn()).toBeTrue();
    expect(service.authChecked()).toBeTrue();
  });

  it('should clear user on failed init', () => {
    apiSpy.me.and.returnValue(throwError(() => new Error('fail')));
    service.init();
    expect(service.user()).toBeNull();
    expect(service.authChecked()).toBeTrue();
  });

  it('should set user after login', () => {
    const loginResponse = { id: 2, email: 'b@c.com', first_name: 'B', last_name: 'C', is_staff: true, totp_enabled: false, avatar_url: null, access: 'tok' };
    apiSpy.login.and.returnValue(of(loginResponse));
    service.login('b@c.com', 'pass').subscribe();
    const { access, ...user } = loginResponse;
    expect(service.user()).toEqual(user);
  });

  it('should clear user on logout', () => {
    const user = { id: 1, email: 'a@b.com', first_name: 'A', last_name: 'B', is_staff: false, totp_enabled: false, avatar_url: null };
    apiSpy.me.and.returnValue(of(user));
    service.init();
    service.logout();
    expect(service.user()).toBeNull();
  });
});
