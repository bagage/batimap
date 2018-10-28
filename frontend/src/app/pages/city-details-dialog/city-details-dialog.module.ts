import {NgModule} from '@angular/core';
import {CityDetailsDialogComponent} from './city-details-dialog.component';
import {MatLibModule} from '../../mat-lib.module';
import {CommonModule} from '@angular/common';
import {SharedComponentsModule} from '../../components/shared-components.module';

@NgModule({
  imports: [
    CommonModule,
    MatLibModule,
    SharedComponentsModule
  ],
  declarations: [CityDetailsDialogComponent],
  entryComponents: [CityDetailsDialogComponent]
})
export class CityDetailsDialogModule { }
