import { Component, inject } from '@angular/core';
import { RouterModule, Router } from "@angular/router";
import { AuthService } from '../../../../core/auth/auth.service';

@Component({
  selector: 'app-boards-page',
  standalone: true,
  imports: [RouterModule],
  templateUrl: './boards-page.component.html',
  styleUrl: './boards-page.component.scss'
})
export class BoardsPageComponent {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);

  logout(): void {
    this.auth.logout();
    this.router.navigate(['login']);
  }
}
