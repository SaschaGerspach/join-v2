import { HttpInterceptorFn, HttpStatusCode } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, throwError } from 'rxjs';
import { AuthService } from '../auth/auth.service';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const router = inject(Router);
  const auth = inject(AuthService);

  return next(req).pipe(
    catchError(err => {
      if (err.status === HttpStatusCode.Unauthorized) {
        auth.clearUser();
        router.navigate(['/login']);
      }
      return throwError(() => err);
    })
  );
};
