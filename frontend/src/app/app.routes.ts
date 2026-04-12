import { Routes } from '@angular/router';
import { LoginPageComponent } from './features/auth/pages/login-page/login-page.component';
import { RegisterPageComponent } from './features/auth/pages/register-page/register-page.component';
import { ForgotPasswordPageComponent } from './features/auth/pages/forgot-password-page/forgot-password-page.component';
import { ResetPasswordPageComponent } from './features/auth/pages/reset-password-page/reset-password-page.component';
import { BoardsPageComponent } from './features/boards/pages/boards-page/boards-page.component';
import { BoardDetailPageComponent } from './features/boards/pages/board-detail-page/board-detail-page.component';
import { ContactsPageComponent } from './features/contacts/pages/contacts-page/contacts-page.component';
import { SummaryPageComponent } from './features/summary/pages/summary-page/summary-page.component';
import { ProfilePageComponent } from './features/profile/pages/profile-page/profile-page.component';
import { ShellComponent } from './layout/shell/shell.component';
import { authGuard } from './core/guards/auth.guard';
import { adminGuard } from './core/guards/admin.guard';
import { NotFoundPageComponent } from './features/not-found/not-found-page.component';
import { AdminPageComponent } from './features/admin/pages/admin-page/admin-page.component';

export const routes: Routes = [
    {path: 'login', title: 'Log in | Join', component: LoginPageComponent},
    {path: 'register', title: 'Sign up | Join', component: RegisterPageComponent},
    {path: 'forgot-password', title: 'Reset Password | Join', component: ForgotPasswordPageComponent},
    {path: 'reset-password/:uid/:token', title: 'Set New Password | Join', component: ResetPasswordPageComponent},

    {
        path: '',
        component: ShellComponent,
        canActivate: [authGuard],
        children: [
                {path: '', pathMatch: 'full', redirectTo: 'summary'},
                {path: 'summary', title: 'Summary | Join', component: SummaryPageComponent},
                {path: 'boards', title: 'Boards | Join', component: BoardsPageComponent},
                {path: 'boards/:id', title: 'Board | Join', component: BoardDetailPageComponent},
                {path: 'contacts', title: 'Contacts | Join', component: ContactsPageComponent},
                {path: 'profile', title: 'Profile | Join', component: ProfilePageComponent},
                {path: 'admin', title: 'Admin | Join', component: AdminPageComponent, canActivate: [adminGuard]},
        ],
    },

    {path: '**', title: 'Not Found | Join', component: NotFoundPageComponent},
];
