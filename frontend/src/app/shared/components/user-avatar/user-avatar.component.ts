import { ChangeDetectionStrategy, Component, computed, input } from '@angular/core';

@Component({
  selector: 'app-user-avatar',
  standalone: true,
  template: `
    @if (avatarUrl()) {
      <img [src]="avatarUrl()" [alt]="initials()" class="avatar-img" [style.width.px]="size()" [style.height.px]="size()" />
    } @else {
      <span class="avatar-initials" [style.width.px]="size()" [style.height.px]="size()" [style.font-size.px]="fontSize()">{{ initials() }}</span>
    }
  `,
  styles: [`
    :host { display: inline-flex; }
    .avatar-img {
      border-radius: 50%;
      object-fit: cover;
    }
    .avatar-initials {
      border-radius: 50%;
      background: var(--color-sidebar-bg, #2a3647);
      color: var(--color-sidebar-text, #fff);
      display: inline-flex;
      align-items: center;
      justify-content: center;
      font-weight: 700;
      text-transform: uppercase;
      flex-shrink: 0;
    }
  `],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class UserAvatarComponent {
  firstName = input('');
  lastName = input('');
  avatarUrl = input<string | null>(null);
  size = input(40);

  initials = computed(() => {
    const f = this.firstName();
    const l = this.lastName();
    return ((f?.[0] ?? '') + (l?.[0] ?? '')).toUpperCase() || '?';
  });

  fontSize = computed(() => this.size() * 0.38);
}
