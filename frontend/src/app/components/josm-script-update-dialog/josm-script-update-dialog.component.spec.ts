import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { JosmScriptUpdateDialogComponent } from './josm-script-update-dialog.component';
import { MatLibModule } from '../../mat-lib.module';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';

describe('JosmScriptUpdateDialogComponent', () => {
    let component: JosmScriptUpdateDialogComponent;
    let fixture: ComponentFixture<JosmScriptUpdateDialogComponent>;

    beforeEach(async(() => {
        TestBed.configureTestingModule({
            declarations: [JosmScriptUpdateDialogComponent],
            imports: [MatLibModule, NoopAnimationsModule]
        }).compileComponents();
    }));

    beforeEach(() => {
        fixture = TestBed.createComponent(JosmScriptUpdateDialogComponent);
        component = fixture.componentInstance;
        fixture.detectChanges();
    });

    it('should create', () => {
        expect(component).toBeTruthy();
    });
});
