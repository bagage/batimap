import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { AboutDialogComponent } from '../components/about-dialog/about-dialog.component';
import { MatLibModule } from '../mat-lib.module';
import { CitiesListModule } from './cities-list/cities-list.module';
import { MapModule } from './map/map.module';

@NgModule({
    imports: [CommonModule, MapModule, CitiesListModule, MatLibModule]
})
export class PagesModule {}
