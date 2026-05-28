import { TestBed } from '@angular/core/testing';
import { of, throwError } from 'rxjs';
import { NotificationService } from './notification.service';
import { NotificationsApiService, AppNotification } from './notifications-api.service';
import { AuthService } from '../auth/auth.service';

describe('NotificationService', () => {
  let service: NotificationService;
  let apiSpy: jasmine.SpyObj<NotificationsApiService>;
  let authSpy: jasmine.SpyObj<AuthService>;

  const mockNotification: AppNotification = {
    id: 1,
    type: 'assignment',
    message: 'Test',
    board_id: 1,
    task_id: 1,
    is_read: false,
    created_at: '2026-01-01T00:00:00Z',
  };

  beforeEach(() => {
    apiSpy = jasmine.createSpyObj('NotificationsApiService', ['getAll', 'markAsRead', 'markAllAsRead']);
    authSpy = jasmine.createSpyObj('AuthService', ['getAccessToken']);
    apiSpy.getAll.and.returnValue(of([]));

    TestBed.configureTestingModule({
      providers: [
        { provide: NotificationsApiService, useValue: apiSpy },
        { provide: AuthService, useValue: authSpy },
      ],
    });
    service = TestBed.inject(NotificationService);
  });

  afterEach(() => service.disconnect());

  it('should start with empty notifications', () => {
    expect(service.notifications()).toEqual([]);
    expect(service.unreadCount()).toBe(0);
  });

  it('should compute unreadCount from notifications', () => {
    const read = { ...mockNotification, id: 2, is_read: true };
    service.notifications.set([mockNotification, read]);
    expect(service.unreadCount()).toBe(1);
  });

  it('should update notification on markAsRead', () => {
    service.notifications.set([mockNotification]);
    const updated = { ...mockNotification, is_read: true };
    apiSpy.markAsRead.and.returnValue(of(updated));

    service.markAsRead(1);

    expect(apiSpy.markAsRead).toHaveBeenCalledWith(1);
    expect(service.notifications()[0].is_read).toBeTrue();
  });

  it('should not crash on markAsRead failure', () => {
    service.notifications.set([mockNotification]);
    apiSpy.markAsRead.and.returnValue(throwError(() => new Error('fail')));

    expect(() => service.markAsRead(1)).not.toThrow();
    expect(service.notifications()[0].is_read).toBeFalse();
  });

  it('should mark all as read', () => {
    const n2 = { ...mockNotification, id: 2 };
    service.notifications.set([mockNotification, n2]);
    apiSpy.markAllAsRead.and.returnValue(of(void 0));

    service.markAllAsRead();

    expect(service.notifications().every(n => n.is_read)).toBeTrue();
  });
});
