import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError, throwError, timeout, TimeoutError } from 'rxjs';
import { TranslateService } from '@ngx-translate/core';
import { ToastService } from '../../shared/services/toast.service';

const REQUEST_TIMEOUT_MS = 30_000;
const UPLOAD_TIMEOUT_MS = 300_000;

export const errorInterceptor: HttpInterceptorFn = (req, next) => {
  const toast = inject(ToastService);
  const translate = inject(TranslateService);

  const isUpload = req.body instanceof FormData;
  const timeoutMs = isUpload ? UPLOAD_TIMEOUT_MS : REQUEST_TIMEOUT_MS;

  return next(req).pipe(
    timeout(timeoutMs),
    catchError((err: HttpErrorResponse | TimeoutError) => {
      if (err instanceof TimeoutError) {
        toast.show(translate.instant('TOAST.REQUEST_TIMEOUT'), 'error');
        return throwError(() => new HttpErrorResponse({ status: 408, statusText: 'Request Timeout' }));
      }
      if (err.status === 0) {
        toast.show(translate.instant('TOAST.NETWORK_ERROR'), 'error');
      } else if (err.status === 401) {
        // handled by auth interceptor
      } else if (err.status === 400) {
        const detail = err.error?.detail;
        if (detail) toast.show(detail, 'error');
      } else if (err.status === 403) {
        toast.show(translate.instant('TOAST.PERMISSION_ERROR'), 'error');
      } else if (err.status >= 500) {
        toast.show(translate.instant('TOAST.SERVER_ERROR'), 'error');
      } else {
        toast.show(translate.instant('TOAST.SOMETHING_WRONG'), 'error');
      }
      return throwError(() => err);
    }),
  );
};
