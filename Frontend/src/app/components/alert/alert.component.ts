import { CommonModule } from '@angular/common';
import { Component, Input, OnInit } from '@angular/core';

@Component({
  selector: 'app-alert',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './alert.component.html',
  styleUrls: ['./alert.component.css']
})
export class AlertComponent implements OnInit {
  @Input() message: string = '';
  @Input() type: 'success' | 'error' = 'success';
  visible = true;

  ngOnInit() {
    const alertDismissed = sessionStorage.getItem('alertDismissed');
    if (alertDismissed) {
      this.visible = false;
    } else {
      setTimeout(() => this.visible = false, 3000);
    }
  }

  dismissAlert() {
    this.visible = false;
    sessionStorage.setItem('alertDismissed', 'true');
  }
}
