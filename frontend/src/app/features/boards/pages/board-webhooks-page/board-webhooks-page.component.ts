import { ChangeDetectionStrategy, Component, DestroyRef, inject, signal, OnInit } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { ActivatedRoute, RouterModule } from '@angular/router';
import { DatePipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { TranslateModule, TranslateService } from '@ngx-translate/core';
import { BoardsApiService } from '../../../../core/boards/boards-api.service';
import { WebhooksApiService, Webhook, WebhookDelivery } from '../../../../core/webhooks/webhooks-api.service';
import { ToastService } from '../../../../shared/services/toast.service';
import { ConfirmDialogComponent } from '../../../../shared/components/confirm-dialog/confirm-dialog.component';

@Component({
  selector: 'app-board-webhooks-page',
  standalone: true,
  imports: [RouterModule, DatePipe, FormsModule, TranslateModule, ConfirmDialogComponent],
  templateUrl: './board-webhooks-page.component.html',
  styleUrl: './board-webhooks-page.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class BoardWebhooksPageComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly destroyRef = inject(DestroyRef);
  private readonly boardsApi = inject(BoardsApiService);
  private readonly webhooksApi = inject(WebhooksApiService);
  private readonly toast = inject(ToastService);
  private readonly translate = inject(TranslateService);

  boardId = signal(0);
  boardTitle = signal('Board');
  loading = signal(true);
  webhooks = signal<Webhook[]>([]);
  availableEvents = signal<string[]>([]);
  deliveries = signal<WebhookDelivery[]>([]);
  selectedWebhookId = signal<number | null>(null);

  showForm = signal(false);
  formUrl = signal('');
  formSecret = signal('');
  formEvents = signal<Set<string>>(new Set());
  editingId = signal<number | null>(null);
  deleteTarget = signal<number | null>(null);

  ngOnInit(): void {
    this.boardId.set(Number(this.route.snapshot.paramMap.get('id')));
    this.boardsApi.getById(this.boardId())
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({ next: b => this.boardTitle.set(b.title) });

    this.webhooksApi.getAvailableEvents()
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({ next: events => this.availableEvents.set(events) });

    this.loadWebhooks();
  }

  loadWebhooks(): void {
    this.webhooksApi.getByBoard(this.boardId())
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: wh => {
          this.webhooks.set(wh);
          this.loading.set(false);
        },
      });
  }

  openCreateForm(): void {
    this.editingId.set(null);
    this.formUrl.set('');
    this.formSecret.set('');
    this.formEvents.set(new Set());
    this.showForm.set(true);
  }

  editWebhook(wh: Webhook): void {
    this.editingId.set(wh.id);
    this.formUrl.set(wh.url);
    this.formSecret.set(wh.secret);
    this.formEvents.set(new Set(wh.events));
    this.showForm.set(true);
  }

  toggleEvent(event: string): void {
    const current = new Set(this.formEvents());
    if (current.has(event)) {
      current.delete(event);
    } else {
      current.add(event);
    }
    this.formEvents.set(current);
  }

  saveWebhook(): void {
    const url = this.formUrl().trim();
    if (!url || this.formEvents().size === 0) return;

    const payload = {
      url,
      secret: this.formSecret(),
      events: [...this.formEvents()],
    };

    const id = this.editingId();
    const obs = id
      ? this.webhooksApi.update(id, payload)
      : this.webhooksApi.create(this.boardId(), payload);

    obs.pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: () => {
        this.showForm.set(false);
        this.loadWebhooks();
        this.toast.show(this.translate.instant('TOAST.WEBHOOK_SAVED'));
      },
    });
  }

  confirmDelete(id: number): void {
    this.deleteTarget.set(id);
  }

  doDelete(): void {
    const id = this.deleteTarget();
    if (!id) return;
    this.webhooksApi.delete(id)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: () => {
          this.deleteTarget.set(null);
          this.loadWebhooks();
          this.toast.show(this.translate.instant('TOAST.WEBHOOK_DELETED'));
        },
      });
  }

  toggleActive(wh: Webhook): void {
    this.webhooksApi.update(wh.id, { is_active: !wh.is_active })
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({ next: () => this.loadWebhooks() });
  }

  viewDeliveries(webhookId: number): void {
    if (this.selectedWebhookId() === webhookId) {
      this.selectedWebhookId.set(null);
      this.deliveries.set([]);
      return;
    }
    this.selectedWebhookId.set(webhookId);
    this.webhooksApi.getDeliveries(webhookId)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({ next: d => this.deliveries.set(d) });
  }

  cancelForm(): void {
    this.showForm.set(false);
  }
}
