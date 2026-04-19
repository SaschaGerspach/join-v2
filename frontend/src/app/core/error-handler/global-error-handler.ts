import { ErrorHandler, Injectable, inject } from '@angular/core';
import { ToastService } from '../../shared/services/toast.service';

@Injectable()
export class GlobalErrorHandler implements ErrorHandler {
  private readonly toast = inject(ToastService);

  handleError(error: unknown): void {
    console.error('Unhandled error:', error);

    const message = error instanceof Error ? error.message : 'An unexpected error occurred.';
    if (!message.includes('ExpressionChangedAfterItHasBeenCheckedError')) {
      this.toast.show('Something went wrong.', 'error');
    }
  }
}
