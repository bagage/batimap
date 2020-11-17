import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';

import { MatLibModule } from '../../mat-lib.module';
import { LoaderComponent } from './loader.component';

describe('LoaderComponent', () => {
    let component: LoaderComponent;
    let fixture: ComponentFixture<LoaderComponent>;

    beforeEach(
        waitForAsync(() => {
            TestBed.configureTestingModule({
                declarations: [LoaderComponent],
                imports: [MatLibModule],
            }).compileComponents();
        })
    );

    beforeEach(() => {
        fixture = TestBed.createComponent(LoaderComponent);
        component = fixture.componentInstance;
        fixture.detectChanges();
    });

    it('should create', () => {
        expect(component).toBeTruthy();
    });
});
