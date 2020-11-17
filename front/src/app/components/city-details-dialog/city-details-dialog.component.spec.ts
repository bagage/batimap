import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';

import { HttpClientTestingModule } from '@angular/common/http/testing';
import { NgModule } from '@angular/core';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { CityDTO } from '../../classes/city.dto';
import { MatLibModule } from '../../mat-lib.module';
import { PipesModule } from '../../pipes/pipes.module';
import { AppConfigService } from '../../services/app-config.service';
import { MockAppConfigService } from '../../services/app-config.service.mock';
import { HowtoDialogComponent } from '../howto-dialog/howto-dialog.component';
import { JosmButtonComponent } from '../josm-button/josm-button.component';
import { CityDetailsDialogComponent } from './city-details-dialog.component';

@NgModule({
    imports: [MatLibModule],
    exports: [HowtoDialogComponent],
    declarations: [HowtoDialogComponent],
    entryComponents: [HowtoDialogComponent],
})
class DialogTestModule {}

describe('CityDetailsDialogComponent', () => {
    let component: CityDetailsDialogComponent;
    let fixture: ComponentFixture<CityDetailsDialogComponent>;

    beforeEach(
        waitForAsync(() => {
            TestBed.configureTestingModule({
                declarations: [CityDetailsDialogComponent, JosmButtonComponent],
                imports: [MatLibModule, HttpClientTestingModule, DialogTestModule, NoopAnimationsModule, PipesModule],
                providers: [
                    { provide: MAT_DIALOG_DATA, useValue: {} },
                    { provide: MatDialogRef, useValue: {} },
                    { provide: AppConfigService, useClass: MockAppConfigService },
                ],
            }).compileComponents();
        })
    );

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
