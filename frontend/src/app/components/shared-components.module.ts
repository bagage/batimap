import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import {JosmButtonComponent} from './josm-button/josm-button.component';
import {MatLibModule} from '../pages/mat-lib.module';

@NgModule({
  imports: [
    CommonModule,
    MatLibModule
  ],
  declarations: [JosmButtonComponent],
  exports: [JosmButtonComponent]
})
export class SharedComponentsModule { }
