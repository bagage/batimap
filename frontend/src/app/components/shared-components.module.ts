import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import {JosmButtonComponent} from './josm-button/josm-button.component';
import {MatLibModule} from '../mat-lib.module';
import { LoaderComponent } from './loader/loader.component';

@NgModule({
  imports: [
    CommonModule,
    MatLibModule
  ],
  declarations: [JosmButtonComponent, LoaderComponent],
  exports: [JosmButtonComponent, LoaderComponent]
})
export class SharedComponentsModule { }
