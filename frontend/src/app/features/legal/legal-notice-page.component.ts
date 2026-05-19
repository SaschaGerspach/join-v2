import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { TranslateModule } from '@ngx-translate/core';
import { LanguageService } from '../../shared/services/language.service';

@Component({
  selector: 'app-legal-notice-page',
  standalone: true,
  imports: [RouterLink, FormsModule, TranslateModule],
  templateUrl: './legal-notice-page.component.html',
  styleUrl: './legal-shared.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class LegalNoticePageComponent {
  readonly lang = inject(LanguageService);
}
