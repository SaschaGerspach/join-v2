import { TestBed, fakeAsync, tick } from '@angular/core/testing';
import { ToastService } from './toast.service';

describe('ToastService', () => {
  let service: ToastService;

  beforeEach(() => {
    service = TestBed.inject(ToastService);
  });

  it('should start with no toasts', () => {
    expect(service.toasts().length).toBe(0);
  });

  it('should add a success toast', () => {
    service.show('Hello');
    expect(service.toasts().length).toBe(1);
    expect(service.toasts()[0].message).toBe('Hello');
    expect(service.toasts()[0].type).toBe('success');
  });

  it('should add an error toast', () => {
    service.show('Oops', 'error');
    expect(service.toasts()[0].type).toBe('error');
  });

  it('should dismiss a toast by id', () => {
    service.show('A');
    service.show('B');
    const id = service.toasts()[0].id;
    service.dismiss(id);
    expect(service.toasts().length).toBe(1);
    expect(service.toasts()[0].message).toBe('B');
  });

  it('should auto-dismiss after 3 seconds', fakeAsync(() => {
    service.show('Temporary');
    expect(service.toasts().length).toBe(1);
    tick(3000);
    expect(service.toasts().length).toBe(0);
  }));
});
