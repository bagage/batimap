import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { JosmButtonComponent } from './josm-button.component';
import { MatLibModule } from '../../mat-lib.module';
import { HttpModule } from '@angular/http';
import { HttpClientTestingModule } from '../../../../node_modules/@angular/common/http/testing';
import { LoaderComponent } from '../loader/loader.component';
import { AppConfigService } from '../../services/app-config.service';
import { MockAppConfigService } from '../../services/app-config.service.mock';

describe('JosmButtonComponent', () => {
    let component: JosmButtonComponent;
    let fixture: ComponentFixture<JosmButtonComponent>;

    beforeEach(async(() => {
        TestBed.configureTestingModule({
            declarations: [JosmButtonComponent, LoaderComponent],
            imports: [MatLibModule, HttpModule, HttpClientTestingModule],
            providers: [
                { provide: AppConfigService, useClass: MockAppConfigService }
            ]
        }).compileComponents();
    }));

    beforeEach(() => {
        fixture = TestBed.createComponent(JosmButtonComponent);
        component = fixture.componentInstance;
        const expected_city = {
            name: '',
            date: '',
            details: null,
            insee: '',
            josm_ready: false
        };
        component.city = expected_city;
        fixture.detectChanges();
    });

    it('should create', () => {
        expect(component).toBeTruthy();
    });
});
