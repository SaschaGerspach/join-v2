import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { TranslateModule } from '@ngx-translate/core';
import { LanguageService } from '../../shared/services/language.service';

@Component({
  selector: 'app-privacy-page',
  standalone: true,
  imports: [RouterLink, FormsModule, TranslateModule],
  templateUrl: './privacy-page.component.html',
  styleUrl: './legal-shared.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class PrivacyPageComponent {
  readonly lang = inject(LanguageService);
}
