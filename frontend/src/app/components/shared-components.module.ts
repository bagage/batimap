import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import {JosmButtonComponent} from './josm-button/josm-button.component';
import {MatLibModule} from '../mat-lib.module';
import { LoaderComponent } from './loader/loader.component';
import {AboutDialogComponent} from './about-dialog/about-dialog.component';
import {MapDateLegendComponent} from './map-date-legend/map-date-legend.component';

@NgModule({
  imports: [
    CommonModule,
    MatLibModule
  ],
  declarations: [JosmButtonComponent, LoaderComponent, AboutDialogComponent, MapDateLegendComponent],
  exports: [JosmButtonComponent, LoaderComponent, AboutDialogComponent, MapDateLegendComponent],
  entryComponents: [AboutDialogComponent]
})
export class SharedComponentsModule { }
