import { Location } from '@angular/common';
import { Component } from '@angular/core';

@Component({
  selector: 'app-back-button',
  imports: [],
  templateUrl: './back-button.component.html',
  styleUrl: './back-button.component.css'
})
export class BackButtonComponent {
  constructor(public location: Location) {}
}
