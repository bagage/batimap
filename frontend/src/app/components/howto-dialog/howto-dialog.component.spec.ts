import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { HowtoDialogComponent } from './howto-dialog.component';

describe('HowtoDialogComponent', () => {
  let component: HowtoDialogComponent;
  let fixture: ComponentFixture<HowtoDialogComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ HowtoDialogComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(HowtoDialogComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
