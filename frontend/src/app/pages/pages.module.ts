import {NgModule} from '@angular/core';
import {CommonModule} from '@angular/common';
import {MapModule} from './map/map.module';
import {CitiesListModule} from './cities-list/cities-list.module';
import { AboutDialogComponent } from './about-dialog/about-dialog.component';
import {MatLibModule} from '../mat-lib.module';

@NgModule({
  imports: [
    CommonModule,
    MapModule,
    CitiesListModule,
    MatLibModule
  ],
  entryComponents: [AboutDialogComponent],
  declarations: [AboutDialogComponent]
})
export class PagesModule { }
