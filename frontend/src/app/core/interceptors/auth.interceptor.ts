import { HttpErrorResponse, HttpInterceptorFn, HttpRequest, HttpStatusCode } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { Observable, catchError, shareReplay, switchMap, throwError } from 'rxjs';
import { AuthService } from '../auth/auth.service';
import { AuthApiService } from '../auth/auth-api.service';
import { environment } from '../../../environments/environment';

const AUTH_SKIP_PATHS = ['/auth/login/', '/auth/token/refresh/', '/auth/register/'];
let refresh$: Observable<string> | null = null;

function withBearer(req: HttpRequest<unknown>, token: string): HttpRequest<unknown> {
  return req.clone({ setHeaders: { Authorization: `Bearer ${token}` } });
}

function isAuthSkipped(url: string): boolean {
  return AUTH_SKIP_PATHS.some((p) => url.includes(p));
}

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const router = inject(Router);
  const auth = inject(AuthService);
  const api = inject(AuthApiService);

  const sameOrigin = req.url.startsWith(environment.apiUrl);
  const token = auth.getAccessToken();
  const outgoing = sameOrigin && token && !isAuthSkipped(req.url) ? withBearer(req, token) : req;

  return next(outgoing).pipe(
    catchError((err: HttpErrorResponse) => {
      if (err.status !== HttpStatusCode.Unauthorized || !sameOrigin || isAuthSkipped(req.url)) {
        return throwError(() => err);
      }

      if (!refresh$) {
        refresh$ = api.refreshToken().pipe(
          switchMap((res) => {
            auth.setAccessToken(res.access);
            return [res.access];
          }),
          catchError((refreshErr) => {
            auth.clearUser();
            router.navigate(['/login']);
            return throwError(() => refreshErr);
          }),
          shareReplay(1),
        );
        refresh$.subscribe({ complete: () => (refresh$ = null), error: () => (refresh$ = null) });
      }

      return refresh$.pipe(switchMap((newToken) => next(withBearer(req, newToken))));
    }),
  );
};
