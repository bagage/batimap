import { NgModule } from '@angular/core';
import { LeafletModule } from '@asymmetrik/ngx-leaflet';

import { CommonModule } from '@angular/common';
import '@bagage/leaflet.restoreview';
import '@bagage/leaflet.vectorgrid';
import 'leaflet';
import 'leaflet-geocoder-ban/dist/leaflet-geocoder-ban';
import 'leaflet-hash';
import { SharedComponentsModule } from '../../components/shared-components.module';
import { MatLibModule } from '../../mat-lib.module';
import { TasksComponent } from './tasks.component';

@NgModule({
    imports: [CommonModule, LeafletModule, MatLibModule, SharedComponentsModule],
    declarations: [TasksComponent],
    exports: [TasksComponent],
})
export class TasksModule {}
