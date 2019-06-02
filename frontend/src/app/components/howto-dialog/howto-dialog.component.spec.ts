import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { HowtoDialogComponent } from './howto-dialog.component';
import { MatLibModule } from '../../mat-lib.module';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';

describe('HowtoDialogComponent', () => {
    let component: HowtoDialogComponent;
    let fixture: ComponentFixture<HowtoDialogComponent>;

    beforeEach(async(() => {
        TestBed.configureTestingModule({
            declarations: [HowtoDialogComponent],
            imports: [MatLibModule, NoopAnimationsModule]
        }).compileComponents();
    }));

    beforeEach(() => {
        fixture = TestBed.createComponent(HowtoDialogComponent);
        component = fixture.componentInstance;
        fixture.detectChanges();
    });

    it('should create', () => {
        expect(component).toBeTruthy();
    });
});
