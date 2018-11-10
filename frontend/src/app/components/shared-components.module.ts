import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import {JosmButtonComponent} from './josm-button/josm-button.component';
import {MatLibModule} from '../mat-lib.module';
import { LoaderComponent } from './loader/loader.component';
import {AboutDialogComponent} from './about-dialog/about-dialog.component';
import { HowtoDialogComponent } from './howto-dialog/howto-dialog.component';
import {MapDateLegendComponent} from './map-date-legend/map-date-legend.component';

@NgModule({
  imports: [
    CommonModule,
    MatLibModule
  ],
  declarations: [JosmButtonComponent, LoaderComponent, AboutDialogComponent, HowtoDialogComponent, MapDateLegendComponent],
  exports: [JosmButtonComponent, LoaderComponent, AboutDialogComponent, HowtoDialogComponent, MapDateLegendComponent],
  entryComponents: [AboutDialogComponent, HowtoDialogComponent]
})
export class SharedComponentsModule { }
