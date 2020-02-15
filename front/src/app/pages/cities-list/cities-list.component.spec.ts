import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { HttpClientTestingModule } from '@angular/common/http/testing';
import { LeafletModule } from '@asymmetrik/ngx-leaflet';
import * as L from 'leaflet';
import { SharedComponentsModule } from '../../components/shared-components.module';
import { MatLibModule } from '../../mat-lib.module';
import { AppConfigService } from '../../services/app-config.service';
import { MockAppConfigService } from '../../services/app-config.service.mock';
import { CitiesListComponent } from './cities-list.component';

describe('CitiesListComponent', () => {
    let component: CitiesListComponent;
    let fixture: ComponentFixture<CitiesListComponent>;

    beforeEach(async(() => {
        TestBed.configureTestingModule({
            declarations: [CitiesListComponent],
            imports: [
                MatLibModule,
                SharedComponentsModule,
                HttpClientTestingModule,
                LeafletModule
            ],
            providers: [
                { provide: AppConfigService, useClass: MockAppConfigService }
            ]
        }).compileComponents();
    }));

    beforeEach(() => {
        fixture = TestBed.createComponent(CitiesListComponent);
        component = fixture.componentInstance;
        component.map = new L.Map(document.createElement('div')).setView(
            [0, 0],
            10
        );
        fixture.detectChanges();
    });

    it('should create', () => {
        expect(component).toBeTruthy();
    });
});
