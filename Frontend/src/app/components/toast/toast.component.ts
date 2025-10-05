import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { Observable } from 'rxjs';
import { Toast, ToastService } from '../../services/toast.service';

@Component({
  selector: 'app-toast',
  templateUrl: './toast.component.html',
  styleUrls: ['./toast.component.css'],
  imports: [CommonModule]
})
export class ToastComponent {
  toasts$: Observable<Toast[]>;
  removingToasts: Set<string> = new Set();

  constructor(private toastService: ToastService) {
    this.toasts$ = this.toastService.toasts$;
  }

  removeToast(id: string): void {
    this.removingToasts.add(id);
    setTimeout(() => {
      this.toastService.remove(id);
      this.removingToasts.delete(id);
    }, 300);
  }

  isRemoving(id: string): boolean {
    return this.removingToasts.has(id);
  }
}