import { Routes } from '@angular/router';
import { ShellComponent } from './layout/shell/shell.component';
import { authGuard } from './core/guards/auth.guard';
import { adminGuard } from './core/guards/admin.guard';

export const routes: Routes = [
    {path: 'login', title: 'Log in | Join', loadComponent: () => import('./features/auth/pages/login-page/login-page.component').then(m => m.LoginPageComponent)},
    {path: 'register', title: 'Sign up | Join', loadComponent: () => import('./features/auth/pages/register-page/register-page.component').then(m => m.RegisterPageComponent)},
    {path: 'forgot-password', title: 'Reset Password | Join', loadComponent: () => import('./features/auth/pages/forgot-password-page/forgot-password-page.component').then(m => m.ForgotPasswordPageComponent)},
    {path: 'reset-password/:uid/:token', title: 'Set New Password | Join', loadComponent: () => import('./features/auth/pages/reset-password-page/reset-password-page.component').then(m => m.ResetPasswordPageComponent)},
    {path: 'verify-email-sent', title: 'Verify Email | Join', loadComponent: () => import('./features/auth/pages/verify-email-sent-page/verify-email-sent-page.component').then(m => m.VerifyEmailSentPageComponent)},
    {path: 'verify-email/:uid/:token', title: 'Verify Email | Join', loadComponent: () => import('./features/auth/pages/verify-email-page/verify-email-page.component').then(m => m.VerifyEmailPageComponent)},

    {
        path: '',
        component: ShellComponent,
        canActivate: [authGuard],
        children: [
                {path: '', pathMatch: 'full', redirectTo: 'summary'},
                {path: 'summary', title: 'Summary | Join', loadComponent: () => import('./features/summary/pages/summary-page/summary-page.component').then(m => m.SummaryPageComponent)},
                {path: 'boards', title: 'Boards | Join', loadComponent: () => import('./features/boards/pages/boards-page/boards-page.component').then(m => m.BoardsPageComponent)},
                {path: 'boards/:id', title: 'Board | Join', loadComponent: () => import('./features/boards/pages/board-detail-page/board-detail-page.component').then(m => m.BoardDetailPageComponent)},
                {path: 'boards/:id/stats', title: 'Board Stats | Join', loadComponent: () => import('./features/boards/pages/board-stats-page/board-stats-page.component').then(m => m.BoardStatsPageComponent)},
                {path: 'boards/:id/activity', title: 'Activity | Join', loadComponent: () => import('./features/boards/pages/board-activity-page/board-activity-page.component').then(m => m.BoardActivityPageComponent)},
                {path: 'boards/:id/archive', title: 'Archive | Join', loadComponent: () => import('./features/boards/pages/board-archive-page/board-archive-page.component').then(m => m.BoardArchivePageComponent)},
                {path: 'contacts', title: 'Contacts | Join', loadComponent: () => import('./features/contacts/pages/contacts-page/contacts-page.component').then(m => m.ContactsPageComponent)},
                {path: 'profile', title: 'Profile | Join', loadComponent: () => import('./features/profile/pages/profile-page/profile-page.component').then(m => m.ProfilePageComponent)},
                {path: 'teams', title: 'Teams | Join', loadComponent: () => import('./features/teams/pages/teams-page/teams-page.component').then(m => m.TeamsPageComponent)},
                {path: 'calendar', title: 'Calendar | Join', loadComponent: () => import('./features/calendar/pages/calendar-page/calendar-page.component').then(m => m.CalendarPageComponent)},
                {path: 'admin', title: 'Admin | Join', loadComponent: () => import('./features/admin/pages/admin-page/admin-page.component').then(m => m.AdminPageComponent), canActivate: [adminGuard]},
        ],
    },

    {path: '**', title: 'Not Found | Join', loadComponent: () => import('./features/not-found/not-found-page.component').then(m => m.NotFoundPageComponent)},
];
