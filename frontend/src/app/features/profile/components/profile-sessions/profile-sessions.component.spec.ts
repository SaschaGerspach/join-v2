import { ComponentFixture, TestBed } from '@angular/core/testing';
import { TranslateModule } from '@ngx-translate/core';
import { of } from 'rxjs';
import { AuthApiService, Session } from '../../../../core/auth/auth-api.service';
import { ToastService } from '../../../../shared/services/toast.service';
import { ProfileSessionsComponent } from './profile-sessions.component';

describe('ProfileSessionsComponent', () => {
  let fixture: ComponentFixture<ProfileSessionsComponent>;
  let component: ProfileSessionsComponent;
  let authApi: jasmine.SpyObj<AuthApiService>;

  const sessions: Session[] = [
    { id: 1, created_at: '2026-09-01T10:00:00Z', expires_at: '2026-09-08T10:00:00Z', is_current: true },
    { id: 2, created_at: '2026-09-02T10:00:00Z', expires_at: '2026-09-09T10:00:00Z', is_current: false },
    { id: 3, created_at: '2026-09-03T10:00:00Z', expires_at: '2026-09-10T10:00:00Z', is_current: false },
  ];

  beforeEach(() => {
    authApi = jasmine.createSpyObj('AuthApiService', ['getSessions', 'revokeSession', 'revokeAllSessions']);
    authApi.getSessions.and.returnValue(of(sessions));
    authApi.revokeSession.and.returnValue(of(undefined));
    authApi.revokeAllSessions.and.returnValue(of(undefined));

    TestBed.configureTestingModule({
      imports: [ProfileSessionsComponent, TranslateModule.forRoot()],
      providers: [
        { provide: AuthApiService, useValue: authApi },
        { provide: ToastService, useValue: jasmine.createSpyObj('ToastService', ['show']) },
      ],
    });
    fixture = TestBed.createComponent(ProfileSessionsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should only offer revoking for other sessions', () => {
    expect(fixture.nativeElement.querySelectorAll('.session-item').length).toBe(3);
    expect(fixture.nativeElement.querySelectorAll('.btn-revoke').length).toBe(2);
  });

  it('should remove a revoked session from the list', () => {
    component.revokeSession(2);
    expect(authApi.revokeSession).toHaveBeenCalledWith(2);
    expect(component.sessions().map(s => s.id)).toEqual([1, 3]);
  });

  it('should keep only the current session after revoking all', () => {
    component.revokeAllSessions();
    expect(component.sessions().map(s => s.id)).toEqual([1]);
  });
});
