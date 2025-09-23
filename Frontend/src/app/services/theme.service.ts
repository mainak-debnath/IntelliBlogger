import { Injectable } from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class ThemeService {

  public currentTheme: 'light' | 'dark';

  constructor() {
    // Load from localStorage or default to light
    this.currentTheme = (localStorage.getItem('theme') as 'light' | 'dark') || 'light';
    this.applyTheme(this.currentTheme);
  }

  toggleTheme(): void {
    this.currentTheme = this.currentTheme === 'dark' ? 'light' : 'dark';
    this.applyTheme(this.currentTheme);
  }

  get theme(): 'light' | 'dark' {
    return this.currentTheme;
  }

  private applyTheme(theme: 'light' | 'dark'): void {
    document.documentElement.setAttribute('data-theme', theme);
    document.body.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
  }
}
