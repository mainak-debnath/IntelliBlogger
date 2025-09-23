import { Directive, ElementRef, HostListener } from '@angular/core';

@Directive({
  selector: '[appTilt]',
  standalone: true
})
export class TiltDirective {
  private container: HTMLElement;

  constructor(private el: ElementRef) {
    this.container = this.el.nativeElement;
  }

  @HostListener('mousemove', ['$event'])
  onMouseMove(event: MouseEvent) {
    const rect = this.container.getBoundingClientRect();
    const x = event.clientX - rect.left - rect.width / 2;
    const y = event.clientY - rect.top - rect.height / 2;

    const tiltX = y / 20;
    const tiltY = -x / 20;

    this.container.style.transform =
      `perspective(1000px) rotateX(${tiltX}deg) rotateY(${tiltY}deg) translateZ(10px)`;
  }

  @HostListener('mouseleave')
  onMouseLeave() {
    this.container.style.transform =
      'perspective(1000px) rotateX(0deg) rotateY(0deg) translateZ(0)';
  }
}
