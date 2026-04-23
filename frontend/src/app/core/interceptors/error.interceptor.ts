import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError, throwError, timeout, TimeoutError } from 'rxjs';
import { TranslateService } from '@ngx-translate/core';
import { ToastService } from '../../shared/services/toast.service';

const REQUEST_TIMEOUT_MS = 30_000;

export const errorInterceptor: HttpInterceptorFn = (req, next) => {
  const toast = inject(ToastService);
  const translate = inject(TranslateService);

  return next(req).pipe(
    timeout(REQUEST_TIMEOUT_MS),
    catchError((err: HttpErrorResponse | TimeoutError) => {
      if (err instanceof TimeoutError) {
        toast.show(translate.instant('TOAST.REQUEST_TIMEOUT'), 'error');
        return throwError(() => new HttpErrorResponse({ status: 408, statusText: 'Request Timeout' }));
      }
      if (err.status === 0) {
        toast.show(translate.instant('TOAST.NETWORK_ERROR'), 'error');
      } else if (err.status === 403) {
        toast.show(translate.instant('TOAST.PERMISSION_ERROR'), 'error');
      } else if (err.status >= 500) {
        toast.show(translate.instant('TOAST.SERVER_ERROR'), 'error');
      }
      return throwError(() => err);
    }),
  );
};
