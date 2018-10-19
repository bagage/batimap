import {async, ComponentFixture, TestBed} from '@angular/core/testing';

import {MapDateLegendComponent} from './map-date-legend.component';
import {MatLibModule} from '../../pages/mat-lib.module';
import {HttpModule} from '@angular/http';
import {HttpClientTestingModule} from '../../../../node_modules/@angular/common/http/testing';
import {LeafletModule} from '@asymmetrik/ngx-leaflet';
import * as L from 'leaflet';
import {AppConfigService} from '../../services/app-config.service';
import {MockAppConfigService} from '../../services/app-config.service.mock';

describe('MapDateLegendComponent', () => {
  let component: MapDateLegendComponent;
  let fixture: ComponentFixture<MapDateLegendComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [MapDateLegendComponent],
      imports: [MatLibModule, HttpModule, HttpClientTestingModule, LeafletModule],
      providers: [
        MapDateLegendComponent,
        {provide: AppConfigService, useClass: MockAppConfigService},
      ],
    })
      .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(MapDateLegendComponent);
    component = fixture.componentInstance;
    component.map = new L.Map(document.createElement('div')).setView([0, 0], 10);
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
