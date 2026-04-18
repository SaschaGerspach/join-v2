import { ChangeDetectionStrategy, Component } from '@angular/core';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-not-found-page',
  standalone: true,
  imports: [RouterLink],
  template: `
    <div class="not-found">
      <h1>404</h1>
      <p>This page does not exist.</p>
      <a routerLink="/">Back to home</a>
    </div>
  `,
  styles: [`
    .not-found {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      height: 100vh;
      gap: 16px;
      font-family: sans-serif;
      text-align: center;
    }
    h1 { font-size: 6rem; margin: 0; color: #ccc; }
    p { font-size: 1.2rem; color: #666; margin: 0; }
    a { color: #2a9d8f; text-decoration: none; font-weight: 500; }
    a:hover { text-decoration: underline; }
  `],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class NotFoundPageComponent {}
