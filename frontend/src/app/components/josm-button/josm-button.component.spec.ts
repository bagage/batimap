import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { JosmButtonComponent } from './josm-button.component';

describe('JosmButtonComponent', () => {
  let component: JosmButtonComponent;
  let fixture: ComponentFixture<JosmButtonComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ JosmButtonComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(JosmButtonComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
