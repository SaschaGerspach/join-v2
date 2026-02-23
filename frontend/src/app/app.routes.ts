import { Routes } from '@angular/router';
import { LoginPageComponent } from './features/auth/pages/login-page/login-page.component';
import { BoardsPageComponent } from './features/boards/pages/boards-page/boards-page.component';   
import { ShellComponent } from './layout/shell/shell.component';
import { authGuard } from './core/guards/auth.guard';             

export const routes: Routes = [
    {path: 'login', component: LoginPageComponent},

    {
        path: '',
        component: ShellComponent,
        canActivate: [authGuard],
        children: [
                {path: 'boards', component: BoardsPageComponent},
        ],
    },

    {path: '', pathMatch: 'full', redirectTo: 'boards'},
];
