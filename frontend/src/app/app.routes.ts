import { Routes } from '@angular/router';
import { LoginPageComponent } from './features/auth/pages/login-page/login-page.component';
import { BoardsPageComponent } from './features/boards/pages/boards-page/boards-page.component';   
import { authGuard } from './core/guards/auth.guard';             

export const routes: Routes = [
    {path: 'login', component: LoginPageComponent},
    {path: 'boards', component: BoardsPageComponent, canActivate: [authGuard]},

    {path: '', pathMatch: 'full', redirectTo: 'login'},
];
