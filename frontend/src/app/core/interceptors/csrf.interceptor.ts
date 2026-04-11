import { HttpInterceptorFn } from '@angular/common/http';

const MUTATING_METHODS = ['POST', 'PUT', 'PATCH', 'DELETE'];

function getCookie(name: string): string | null {
    const match = document.cookie.match(new RegExp('(?:^|; )' + name + '=([^;]*)'));
    return match ? decodeURIComponent(match[1]) : null;
}

export const csrfInterceptor: HttpInterceptorFn = (req, next) => {
    if (!MUTATING_METHODS.includes(req.method)) {
        return next(req);
    }

    const token = getCookie('csrftoken');
    if (!token) {
        return next(req);
    }

    return next(req.clone({ setHeaders: { 'X-CSRFToken': token } }));
};
