import { ChangeDetectionStrategy, Component, DestroyRef, inject, signal, OnInit } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormsModule } from '@angular/forms';
import { TeamsApiService, Team, TeamMember } from '../../../../core/teams/teams-api.service';
import { ToastService } from '../../../../shared/services/toast.service';
import { ConfirmDialogComponent } from '../../../../shared/components/confirm-dialog/confirm-dialog.component';
import { LoadingSpinnerComponent } from '../../../../shared/components/loading-spinner/loading-spinner.component';

@Component({
  selector: 'app-teams-page',
  standalone: true,
  imports: [FormsModule, ConfirmDialogComponent, LoadingSpinnerComponent],
  templateUrl: './teams-page.component.html',
  styleUrl: './teams-page.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class TeamsPageComponent implements OnInit {
  private readonly teamsApi = inject(TeamsApiService);
  private readonly toast = inject(ToastService);
  private readonly destroyRef = inject(DestroyRef);

  teams = signal<Team[]>([]);
  loading = signal(true);
  newTeamName = '';
  showCreateForm = signal(false);

  expandedTeamId = signal<number | null>(null);
  teamMembers = signal<TeamMember[]>([]);
  inviteEmail = '';

  pendingDeleteTeamId = signal<number | null>(null);

  ngOnInit(): void {
    this.teamsApi.getAll().pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: teams => { this.teams.set(teams); this.loading.set(false); },
      error: () => { this.toast.show('Failed to load teams.', 'error'); this.loading.set(false); },
    });
  }

  createTeam(): void {
    const name = this.newTeamName.trim();
    if (!name) return;
    this.teamsApi.create(name).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: team => {
        this.teams.update(list => [team, ...list]);
        this.newTeamName = '';
        this.showCreateForm.set(false);
        this.toast.show('Team created.');
      },
      error: () => this.toast.show('Failed to create team.', 'error'),
    });
  }

  toggleExpand(teamId: number): void {
    if (this.expandedTeamId() === teamId) {
      this.expandedTeamId.set(null);
      return;
    }
    this.expandedTeamId.set(teamId);
    this.teamMembers.set([]);
    this.teamsApi.getMembers(teamId).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: members => this.teamMembers.set(members),
      error: () => this.toast.show('Failed to load members.', 'error'),
    });
  }

  inviteMember(): void {
    const teamId = this.expandedTeamId();
    if (!teamId) return;
    const email = this.inviteEmail.trim();
    if (!email) return;
    this.teamsApi.inviteMember(teamId, email).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: member => {
        this.teamMembers.update(list => list.some(m => m.user_id === member.user_id) ? list : [...list, member]);
        this.inviteEmail = '';
        this.toast.show('Member invited.');
      },
      error: (err) => this.toast.show(err?.error?.detail ?? 'Failed to invite.', 'error'),
    });
  }

  removeMember(userId: number): void {
    const teamId = this.expandedTeamId();
    if (!teamId) return;
    this.teamsApi.removeMember(teamId, userId).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: () => {
        this.teamMembers.update(list => list.filter(m => m.user_id !== userId));
        this.toast.show('Member removed.');
      },
      error: () => this.toast.show('Failed to remove member.', 'error'),
    });
  }

  changeRole(userId: number, role: string): void {
    const teamId = this.expandedTeamId();
    if (!teamId) return;
    this.teamsApi.patchMemberRole(teamId, userId, role).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: updated => this.teamMembers.update(list => list.map(m => m.user_id === updated.user_id ? updated : m)),
      error: () => this.toast.show('Failed to update role.', 'error'),
    });
  }

  deleteTeam(id: number): void {
    this.pendingDeleteTeamId.set(id);
  }

  confirmDeleteTeam(): void {
    const id = this.pendingDeleteTeamId();
    if (!id) return;
    this.pendingDeleteTeamId.set(null);
    this.teamsApi.delete(id).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: () => {
        this.teams.update(list => list.filter(t => t.id !== id));
        if (this.expandedTeamId() === id) this.expandedTeamId.set(null);
        this.toast.show('Team deleted.');
      },
      error: () => this.toast.show('Failed to delete team.', 'error'),
    });
  }
}
