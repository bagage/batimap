import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { MapDateLegendComponent } from './map-date-legend.component';

describe('MapDateLegendComponent', () => {
  let component: MapDateLegendComponent;
  let fixture: ComponentFixture<MapDateLegendComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ MapDateLegendComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(MapDateLegendComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
