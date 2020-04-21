import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { CountPipe } from './count.pipe';
import { LegendPipe } from './legend.pipe';
import { MapPipe } from './map.pipe';

@NgModule({
    declarations: [CountPipe, LegendPipe, MapPipe],
    exports: [CountPipe, LegendPipe, MapPipe],
    imports: [CommonModule],
})
export class PipesModule {}
