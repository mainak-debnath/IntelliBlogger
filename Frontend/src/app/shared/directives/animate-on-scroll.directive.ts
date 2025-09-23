import { Directive, ElementRef, OnInit, Renderer2 } from '@angular/core';

@Directive({
  selector: '[appAnimateOnScroll]'
})
export class AnimateOnScrollDirective implements OnInit {
  private observer!: IntersectionObserver;

  constructor(private el: ElementRef, private renderer: Renderer2) {}

  ngOnInit(): void {
    if ('IntersectionObserver' in window) {
      this.observer = new IntersectionObserver(entries => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            this.renderer.addClass(this.el.nativeElement, 'is-visible');
            this.observer.unobserve(this.el.nativeElement);
          }
        });
      }, { threshold: 0.1 });

      this.observer.observe(this.el.nativeElement);
    } else {
      // Fallback: just show immediately
      this.renderer.addClass(this.el.nativeElement, 'is-visible');
    }
  }
}
