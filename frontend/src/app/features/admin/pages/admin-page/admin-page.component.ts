import { ChangeDetectionStrategy, Component } from '@angular/core';
import { TranslateModule } from '@ngx-translate/core';
import { environment } from '../../../../../environments/environment';
import { AdminStatsComponent } from '../../components/admin-stats/admin-stats.component';
import { AdminAuditLogComponent } from '../../components/admin-audit-log/admin-audit-log.component';
import { AdminBoardActivityComponent } from '../../components/admin-board-activity/admin-board-activity.component';

@Component({
  selector: 'app-admin-page',
  standalone: true,
  imports: [TranslateModule, AdminStatsComponent, AdminAuditLogComponent, AdminBoardActivityComponent],
  templateUrl: './admin-page.component.html',
  styleUrl: './admin-page.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AdminPageComponent {
  readonly djangoAdminUrl = `${environment.apiUrl}/manage/`;
}
