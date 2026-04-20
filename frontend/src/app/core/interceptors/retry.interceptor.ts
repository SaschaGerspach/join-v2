import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { retry, timer } from 'rxjs';

export const retryInterceptor: HttpInterceptorFn = (req, next) => {
  if (req.method === 'GET') {
    return next(req).pipe(
      retry({
        count: 2,
        delay: (error, retryCount) => {
          if (error instanceof HttpErrorResponse && error.status === 0) {
            return timer(1000 * retryCount);
          }
          throw error;
        },
      }),
    );
  }

  return next(req).pipe(
    retry({
      count: 1,
      delay: (error) => {
        if (error instanceof HttpErrorResponse && error.status === 0) {
          return timer(1500);
        }
        throw error;
      },
    }),
  );
};
