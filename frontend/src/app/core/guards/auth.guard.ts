import { inject } from "@angular/core";
import { CanActivateChildFn, Router } from "@angular/router";
import { AuthService } from "../auth/auth.service";
import { toObservable } from '@angular/core/rxjs-interop';
import { filter, map, take } from "rxjs";

export const authGuard: CanActivateChildFn = () => {
    const auth = inject(AuthService);
    const router = inject(Router);

    return toObservable(auth.authChecked).pipe(
        filter((checked) => checked === true),
        take(1),
        map(() => (auth.isLoggedIn() ? true : router.parseUrl('/login')))
    );
};