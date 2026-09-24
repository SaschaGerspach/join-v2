import { ComponentFixture, TestBed } from '@angular/core/testing';
import { TranslateModule } from '@ngx-translate/core';
import { of } from 'rxjs';
import { AuthService } from '../../../../core/auth/auth.service';
import { AuthApiService } from '../../../../core/auth/auth-api.service';
import { ToastService } from '../../../../shared/services/toast.service';
import { ProfileTwoFactorComponent } from './profile-two-factor.component';

describe('ProfileTwoFactorComponent', () => {
  let fixture: ComponentFixture<ProfileTwoFactorComponent>;
  let component: ProfileTwoFactorComponent;
  let authApi: jasmine.SpyObj<AuthApiService>;

  function create(totpEnabled: boolean): void {
    TestBed.configureTestingModule({
      imports: [ProfileTwoFactorComponent, TranslateModule.forRoot()],
      providers: [
        { provide: AuthService, useValue: { user: () => ({ totp_enabled: totpEnabled }) } },
        { provide: AuthApiService, useValue: authApi },
        { provide: ToastService, useValue: jasmine.createSpyObj('ToastService', ['show']) },
      ],
    });
    fixture = TestBed.createComponent(ProfileTwoFactorComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  }

  beforeEach(() => {
    authApi = jasmine.createSpyObj('AuthApiService', ['totpSetup', 'totpConfirm', 'totpDisable']);
    authApi.totpConfirm.and.returnValue(of(undefined));
    authApi.totpDisable.and.returnValue(of(undefined));
  });

  it('should take the initial state from the logged-in user', () => {
    create(true);
    expect(component.totpEnabled()).toBeTrue();
  });

  it('should reject confirmation codes that are not six digits', () => {
    create(false);
    component.totpConfirmCode.set('123');
    component.confirmTotp();
    expect(authApi.totpConfirm).not.toHaveBeenCalled();
    expect(component.totpError()).toBeTruthy();
  });

  it('should enable 2FA after a valid confirmation', () => {
    create(false);
    component.totpConfirmCode.set('123456');
    component.confirmTotp();
    expect(authApi.totpConfirm).toHaveBeenCalledWith('123456');
    expect(component.totpEnabled()).toBeTrue();
  });

  it('should require the password before disabling', () => {
    create(true);
    component.totpDisableCode.set('123456');
    component.disableTotp();
    expect(authApi.totpDisable).not.toHaveBeenCalled();

    component.totpDisablePassword.set('secret');
    component.disableTotp();
    expect(authApi.totpDisable).toHaveBeenCalledWith('secret', '123456');
    expect(component.totpEnabled()).toBeFalse();
  });
});
