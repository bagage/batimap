import {async, ComponentFixture, TestBed} from '@angular/core/testing';

import {MapDateLegendComponent} from './map-date-legend.component';
import {MatLibModule} from '../../pages/mat-lib.module';
import {HttpModule} from '@angular/http';
import {HttpClientTestingModule} from '../../../../node_modules/@angular/common/http/testing';
import {LeafletModule} from '@asymmetrik/ngx-leaflet';
import * as L from 'leaflet';
import {AppConfigService} from 'src/app/services/app-config.service';

class MockAppConfigService {
  getConfig() {
    return {
      'backendServerUrl': 'http://localhost:5000/',
      'tilesServerUrl': 'http://localhost:9999/maps/batimap/{z}/{x}/{y}.vector.pbf'
    };
  }
}

describe('MapDateLegendComponent', () => {
  let component: MapDateLegendComponent;
  let fixture: ComponentFixture<MapDateLegendComponent>;
  let service: AppConfigService;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [MapDateLegendComponent],
      imports: [MatLibModule, HttpModule, HttpClientTestingModule, LeafletModule],
      providers: [ MapDateLegendComponent,
        {provide: AppConfigService, useValue: MockAppConfigService},
      ],
    })
      .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(MapDateLegendComponent);
    component = fixture.componentInstance;
    service = TestBed.get(AppConfigService);
    console.log(service);

    service.getConfig();
    component.map = new L.Map(document.createElement('div')).setView([0, 0], 10);
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(service).toBeTruthy();
    expect(component).toBeTruthy();
  });
});
