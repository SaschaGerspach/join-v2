import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { EMPTY } from 'rxjs';
import { TranslateService } from '@ngx-translate/core';
import { OfflineQueueService } from '../offline/offline-queue.service';
import { ToastService } from '../../shared/services/toast.service';

const WRITE_METHODS = new Set(['POST', 'PUT', 'PATCH', 'DELETE']);

export const offlineInterceptor: HttpInterceptorFn = (req, next) => {
  if (!navigator.onLine && WRITE_METHODS.has(req.method)) {
    const queue = inject(OfflineQueueService);
    const toast = inject(ToastService);
    const translate = inject(TranslateService);

    queue.enqueue(req.method, req.urlWithParams, req.body);
    toast.show(translate.instant('TOAST.OFFLINE_CHANGE_QUEUED'));
    return EMPTY;
  }
  return next(req);
};
