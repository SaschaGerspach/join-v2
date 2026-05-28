import { inject } from "@angular/core";
import { CanActivateFn, Router } from "@angular/router";
import { AuthService } from "../auth/auth.service";
import { toObservable } from '@angular/core/rxjs-interop';
import { filter, map, take } from "rxjs";

export const authGuard: CanActivateFn = (route, state) => {
    const auth = inject(AuthService);
    const router = inject(Router);

    return toObservable(auth.authChecked).pipe(
        filter((checked) => checked === true),
        take(1),
        map(() => {
            if (auth.isLoggedIn()) return true;
            const tree = router.parseUrl('/login');
            tree.queryParams = { returnUrl: state.url };
            return tree;
        })
    );
};