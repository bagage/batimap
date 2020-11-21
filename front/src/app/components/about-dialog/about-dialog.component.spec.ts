import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';

import { MatDialogRef } from '@angular/material/dialog';
import { MatLibModule } from '../../mat-lib.module';
import { AboutDialogComponent } from './about-dialog.component';

describe('AboutDialogComponent', () => {
    let component: AboutDialogComponent;
    let fixture: ComponentFixture<AboutDialogComponent>;

    beforeEach(
        waitForAsync(() => {
            TestBed.configureTestingModule({
                declarations: [AboutDialogComponent],
                imports: [MatLibModule],
                providers: [{ provide: MatDialogRef, useValue: {} }],
            }).compileComponents();
        })
    );

    beforeEach(() => {
        fixture = TestBed.createComponent(AboutDialogComponent);
        component = fixture.componentInstance;
        fixture.detectChanges();
    });

    it('should create', () => {
        expect(component).toBeTruthy();
    });
});
