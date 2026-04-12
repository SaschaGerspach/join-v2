import { inject } from "@angular/core";
import { CanActivateFn, Router } from "@angular/router";
import { AuthService } from "../auth/auth.service";
import { toObservable } from '@angular/core/rxjs-interop';
import { filter, map, take } from "rxjs";

export const adminGuard: CanActivateFn = () => {
    const auth = inject(AuthService);
    const router = inject(Router);

    return toObservable(auth.authChecked).pipe(
        filter((checked) => checked === true),
        take(1),
        map(() => {
            const user = auth.user();
            if (user?.is_staff) return true;
            return user ? router.parseUrl('/summary') : router.parseUrl('/login');
        })
    );
};
