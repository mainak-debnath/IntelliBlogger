import { Component, DebugElement } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { AnimateOnScrollDirective } from './animate-on-scroll.directive';

@Component({
  template: `<div appAnimateOnScroll>Test content</div>`
})
class TestComponent {}

describe('AnimateOnScrollDirective', () => {
  let component: TestComponent;
  let fixture: ComponentFixture<TestComponent>;
  let directiveEl: DebugElement;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [AnimateOnScrollDirective, TestComponent]
    }).compileComponents();

    fixture = TestBed.createComponent(TestComponent);
    component = fixture.componentInstance;
    directiveEl = fixture.debugElement.query(By.directive(AnimateOnScrollDirective));
  });

  it('should create an instance', () => {
    const directive = directiveEl.injector.get(AnimateOnScrollDirective);
    expect(directive).toBeTruthy();
  });

  it('should apply directive to element', () => {
    expect(directiveEl).not.toBeNull();
  });
});