import { HttpErrorResponse, HttpInterceptorFn, HttpRequest, HttpStatusCode } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, switchMap, throwError } from 'rxjs';
import { AuthService } from '../auth/auth.service';
import { environment } from '../../../environments/environment';

const AUTH_SKIP_PATHS = ['/auth/login/', '/auth/token/refresh/', '/auth/register/'];
const SESSION_PROBE_PATH = '/auth/me/';

function withBearer(req: HttpRequest<unknown>, token: string): HttpRequest<unknown> {
  return req.clone({ setHeaders: { Authorization: `Bearer ${token}` } });
}

function isAuthSkipped(url: string): boolean {
  return AUTH_SKIP_PATHS.some((p) => url.endsWith(p));
}

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const router = inject(Router);
  const auth = inject(AuthService);

  // A bare prefix check would also match hosts like `<apiUrl>.evil.com` and leak the token there.
  const sameOrigin = req.url === environment.apiUrl || req.url.startsWith(`${environment.apiUrl}/`);
  const token = auth.getAccessToken();
  const outgoing = sameOrigin && token && !isAuthSkipped(req.url) ? withBearer(req, token) : req;

  return next(outgoing).pipe(
    catchError((err: HttpErrorResponse) => {
      if (err.status !== HttpStatusCode.Unauthorized || !sameOrigin || isAuthSkipped(req.url)) {
        return throwError(() => err);
      }

      return auth.refreshAccessToken().pipe(
        catchError((refreshErr) => {
          // The startup session probe fails for every logged-out visitor, including on public
          // pages like register or password reset; authGuard already redirects protected routes.
          if (!req.url.endsWith(SESSION_PROBE_PATH)) {
            router.navigate(['/login']);
          }
          return throwError(() => refreshErr);
        }),
        switchMap((newToken) => next(withBearer(req, newToken))),
      );
    }),
  );
};
