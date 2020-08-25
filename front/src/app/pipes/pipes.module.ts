import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { CountPipe } from './count.pipe';
import { LegendPipe } from './legend.pipe';
import { MapPipe } from './map.pipe';
import { SortedPipe } from './sorted.pipe';

@NgModule({
    declarations: [CountPipe, LegendPipe, MapPipe, SortedPipe],
    exports: [CountPipe, LegendPipe, MapPipe, SortedPipe],
    imports: [CommonModule],
})
export class PipesModule {}
