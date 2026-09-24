import { TestBed } from '@angular/core/testing';
import { ActivatedRoute, provideRouter, Router } from '@angular/router';
import { NgForm } from '@angular/forms';
import { TranslateModule } from '@ngx-translate/core';
import { of } from 'rxjs';
import { AuthService } from '../../../../core/auth/auth.service';
import { LoginPageComponent } from './login-page.component';

describe('LoginPageComponent', () => {
  let router: Router;
  const queryParams: Record<string, unknown> = {};
  const validForm = { invalid: false } as NgForm;

  beforeEach(() => {
    const authSpy = jasmine.createSpyObj('AuthService', ['login']);
    authSpy.login.and.returnValue(of({}));

    TestBed.configureTestingModule({
      imports: [LoginPageComponent, TranslateModule.forRoot()],
      providers: [
        provideRouter([]),
        { provide: AuthService, useValue: authSpy },
        { provide: ActivatedRoute, useValue: { snapshot: { queryParams } } },
      ],
    });
    router = TestBed.inject(Router);
    spyOn(router, 'navigateByUrl').and.resolveTo(true);
  });

  afterEach(() => delete queryParams['returnUrl']);

  function loginWithReturnUrl(returnUrl: unknown): void {
    if (returnUrl !== undefined) queryParams['returnUrl'] = returnUrl;
    TestBed.createComponent(LoginPageComponent).componentInstance.login(validForm);
  }

  it('should navigate to an in-app returnUrl', () => {
    loginWithReturnUrl('/boards/42?task=7');
    expect(router.navigateByUrl).toHaveBeenCalledWith('/boards/42?task=7');
  });

  it('should fall back to boards without a returnUrl', () => {
    loginWithReturnUrl(undefined);
    expect(router.navigateByUrl).toHaveBeenCalledWith('/boards');
  });

  for (const unsafe of ['https://evil.com', '//evil.com', '/\\evil.com', 'javascript:alert(1)', ['/a', '/b']]) {
    it(`should ignore the unsafe returnUrl ${JSON.stringify(unsafe)}`, () => {
      loginWithReturnUrl(unsafe);
      expect(router.navigateByUrl).toHaveBeenCalledWith('/boards');
    });
  }
});
