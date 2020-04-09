import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { MatLibModule } from '../mat-lib.module';
import { MapModule } from './map/map.module';

@NgModule({
    imports: [CommonModule, MapModule, MatLibModule]
})
export class PagesModule {}
