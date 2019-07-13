import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { NgModule } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { HttpClientTestingModule } from '../../../../node_modules/@angular/common/http/testing';
import { CityDTO } from '../../classes/city.dto';
import { MatLibModule } from '../../mat-lib.module';
import { AppConfigService } from '../../services/app-config.service';
import { MockAppConfigService } from '../../services/app-config.service.mock';
import { HowtoDialogComponent } from '../howto-dialog/howto-dialog.component';
import { JosmButtonComponent } from '../josm-button/josm-button.component';
import { CityDetailsDialogComponent } from './city-details-dialog.component';

@NgModule({
    imports: [MatLibModule],
    exports: [HowtoDialogComponent],
    declarations: [HowtoDialogComponent],
    entryComponents: [HowtoDialogComponent]
})
class DialogTestModule {}

describe('CityDetailsDialogComponent', () => {
    let component: CityDetailsDialogComponent;
    let fixture: ComponentFixture<CityDetailsDialogComponent>;

    beforeEach(async(() => {
        TestBed.configureTestingModule({
            declarations: [CityDetailsDialogComponent, JosmButtonComponent],
            imports: [
                MatLibModule,
                HttpClientTestingModule,
                DialogTestModule,
                NoopAnimationsModule
            ],
            providers: [
                { provide: MAT_DIALOG_DATA, useValue: {} },
                { provide: MatDialogRef, useValue: {} },
                { provide: AppConfigService, useClass: MockAppConfigService }
            ]
        }).compileComponents();
    }));

    beforeEach(() => {
        fixture = TestBed.createComponent(CityDetailsDialogComponent);
        component = fixture.componentInstance;
        component.city = new CityDTO();
        fixture.detectChanges();
    });

    it('should create', () => {
        expect(component).toBeTruthy();
    });
});
