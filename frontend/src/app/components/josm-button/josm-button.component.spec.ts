import {async, ComponentFixture, TestBed} from '@angular/core/testing';

import {JosmButtonComponent} from './josm-button.component';
import {MatLibModule} from '../../pages/mat-lib.module';
import {HttpModule} from '@angular/http';
import {HttpClientTestingModule} from '../../../../node_modules/@angular/common/http/testing';
import {LoaderComponent} from '../loader/loader.component';

describe('JosmButtonComponent', () => {
  let component: JosmButtonComponent;
  let fixture: ComponentFixture<JosmButtonComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [JosmButtonComponent, LoaderComponent],
      imports: [MatLibModule, HttpModule, HttpClientTestingModule]
    })
      .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(JosmButtonComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
