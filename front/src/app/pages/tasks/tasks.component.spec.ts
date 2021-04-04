import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { MatLibModule } from '../../mat-lib.module';
import { AppConfigService } from '../../services/app-config.service';
import { MockAppConfigService } from '../../services/app-config.service.mock';

import { TasksComponent } from './tasks.component';

describe('TasksComponent', () => {
    let component: TasksComponent;
    let fixture: ComponentFixture<TasksComponent>;

    beforeEach(async () => {
        await TestBed.configureTestingModule({
            declarations: [TasksComponent],
            imports: [MatLibModule, HttpClientTestingModule],
            providers: [{ provide: AppConfigService, useClass: MockAppConfigService }],
        }).compileComponents();
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(TasksComponent);
        component = fixture.componentInstance;
        fixture.detectChanges();
    });

    it('should create', () => {
        expect(component).toBeTruthy();
    });
});
