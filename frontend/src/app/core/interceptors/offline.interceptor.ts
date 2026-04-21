import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { EMPTY } from 'rxjs';
import { OfflineQueueService } from '../offline/offline-queue.service';
import { ToastService } from '../../shared/services/toast.service';

const WRITE_METHODS = new Set(['POST', 'PUT', 'PATCH', 'DELETE']);

export const offlineInterceptor: HttpInterceptorFn = (req, next) => {
  if (!navigator.onLine && WRITE_METHODS.has(req.method)) {
    const queue = inject(OfflineQueueService);
    const toast = inject(ToastService);

    queue.enqueue(req.method, req.urlWithParams, req.body);
    toast.show('You are offline. Change queued for sync.');
    return EMPTY;
  }
  return next(req);
};
