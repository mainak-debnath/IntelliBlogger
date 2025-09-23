import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { RouterModule } from '@angular/router';
import { AuthService } from '../../services/auth.service';
import { ThemeService } from '../../services/theme.service';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './home.component.html',
  styleUrl: './home.component.css'
})
export class HomeComponent implements OnInit {
  isYearly: boolean = false;
  isMobileMenuOpen: boolean = false;

  constructor(public themeService: ThemeService,
    private auth: AuthService
  ) { }

  get isAuthenticated(): boolean {
    return this.auth.isAuthenticated();
  }

  ngOnInit(): void {

  }

  togglePricing(event: any): void {
    this.isYearly = event.target.checked;
  }

  toggleTheme(): void {
    this.themeService.toggleTheme();
  }

  toggleMobileMenu(): void {
    this.isMobileMenuOpen = !this.isMobileMenuOpen;
  }

  closeMobileMenu(): void {
    this.isMobileMenuOpen = false;
  }
}
