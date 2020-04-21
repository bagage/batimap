import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { HttpClientTestingModule } from '@angular/common/http/testing';
import { MatLibModule } from '../../mat-lib.module';
import { AppConfigService } from '../../services/app-config.service';
import { MockAppConfigService } from '../../services/app-config.service.mock';
import { LoaderComponent } from '../loader/loader.component';
import { JosmButtonComponent } from './josm-button.component';

describe('JosmButtonComponent', () => {
    let component: JosmButtonComponent;
    let fixture: ComponentFixture<JosmButtonComponent>;

    beforeEach(async(() => {
        TestBed.configureTestingModule({
            declarations: [JosmButtonComponent, LoaderComponent],
            imports: [MatLibModule, HttpClientTestingModule],
            providers: [{ provide: AppConfigService, useClass: MockAppConfigService }],
        }).compileComponents();
    }));

    beforeEach(() => {
        fixture = TestBed.createComponent(JosmButtonComponent);
        component = fixture.componentInstance;
        const expectedCity = {
            name: '',
            date: '',
            details: undefined,
            insee: '',
            josm_ready: false,
        };
        component.city = expectedCity;
        fixture.detectChanges();
    });

    it('should create', () => {
        expect(component).toBeTruthy();
    });
});
