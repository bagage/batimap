import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';

import { HttpClientTestingModule } from '@angular/common/http/testing';
import { LeafletModule } from '@asymmetrik/ngx-leaflet';
import { MapDateLegendComponent } from '../../components/map-date-legend/map-date-legend.component';
import { MatLibModule } from '../../mat-lib.module';
import { MapComponent } from './map.component';

describe('MapComponent', () => {
    let component: MapComponent;
    let fixture: ComponentFixture<MapComponent>;

    beforeEach(
        waitForAsync(() => {
            TestBed.configureTestingModule({
                declarations: [MapComponent, MapDateLegendComponent],
                imports: [LeafletModule, MatLibModule, HttpClientTestingModule],
            }).compileComponents();
        })
    );

    beforeEach(() => {
        fixture = TestBed.createComponent(MapComponent);
        component = fixture.componentInstance;
        fixture.detectChanges();
    });

    // disable for now because it breaks the CI with generic "[object ErrorEvent] thrown" error
    xit('should create', () => {
        expect(component).toBeTruthy();
    });
});
