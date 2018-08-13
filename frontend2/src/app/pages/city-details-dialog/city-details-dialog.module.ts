import {NgModule} from '@angular/core';
import {CityDetailsDialogComponent} from './city-details-dialog.component';
import {MatLibModule} from '../mat-lib.module';
import {CommonModule} from '@angular/common';

@NgModule({
  imports: [
    CommonModule,
    MatLibModule
  ],
  declarations: [CityDetailsDialogComponent],
  entryComponents: [CityDetailsDialogComponent]
})
export class CityDetailsDialogModule { }
