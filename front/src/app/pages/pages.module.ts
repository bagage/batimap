import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { MatLibModule } from '../mat-lib.module';
import { MapModule } from './map/map.module';
import { TasksModule } from './tasks/tasks.module';

@NgModule({
    imports: [CommonModule, MapModule, MatLibModule, TasksModule],
})
export class PagesModule {}
