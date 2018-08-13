import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { CityDetailsDialogComponent } from './city-details-dialog.component';

describe('CityDetailsDialogComponent', () => {
  let component: CityDetailsDialogComponent;
  let fixture: ComponentFixture<CityDetailsDialogComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ CityDetailsDialogComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(CityDetailsDialogComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
