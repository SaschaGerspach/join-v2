import { ErrorHandler, Injectable, inject } from '@angular/core';
import { ToastService } from '../../shared/services/toast.service';
import { environment } from '../../../environments/environment';

@Injectable()
export class GlobalErrorHandler implements ErrorHandler {
  private readonly toast = inject(ToastService);

  handleError(error: unknown): void {
    console.error('Unhandled error:', error);

    const message = error instanceof Error ? error.message : 'An unexpected error occurred.';
    if (!message.includes('ExpressionChangedAfterItHasBeenCheckedError')) {
      this.toast.show('Something went wrong.', 'error');
    }

    if (environment.sentryDsn && error instanceof Error) {
      this.reportToSentry(error);
    }
  }

  private reportToSentry(error: Error): void {
    import('@sentry/browser').then(Sentry => {
      Sentry.captureException(error);
    }).catch(() => {});
  }
}
