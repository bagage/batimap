import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';

import { HttpClientTestingModule } from '@angular/common/http/testing';
import { LeafletModule } from '@asymmetrik/ngx-leaflet';
import { MatLibModule } from '../../mat-lib.module';
import { AppConfigService } from '../../services/app-config.service';
import { MockAppConfigService } from '../../services/app-config.service.mock';
import { LoaderComponent } from '../loader/loader.component';
import { MapDateLegendComponent } from './map-date-legend.component';

import * as L from 'leaflet';

describe('MapDateLegendComponent', () => {
    let component: MapDateLegendComponent;
    let fixture: ComponentFixture<MapDateLegendComponent>;

    beforeEach(
        waitForAsync(() => {
            TestBed.configureTestingModule({
                declarations: [MapDateLegendComponent, LoaderComponent],
                imports: [MatLibModule, HttpClientTestingModule, LeafletModule],
                providers: [MapDateLegendComponent, { provide: AppConfigService, useClass: MockAppConfigService }],
            }).compileComponents();
        })
    );

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
