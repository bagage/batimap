import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { AnyPipe } from './any.pipe';
import { BuildingsRatioPipe } from './buildings-ratio.pipe';
import { CountPipe } from './count.pipe';
import { LegendPipe } from './legend.pipe';
import { MapPipe } from './map.pipe';
import { SortedPipe } from './sorted.pipe';

@NgModule({
    declarations: [CountPipe, LegendPipe, AnyPipe, MapPipe, SortedPipe, BuildingsRatioPipe],
    exports: [CountPipe, LegendPipe, AnyPipe, MapPipe, SortedPipe, BuildingsRatioPipe],
    imports: [CommonModule],
})
export class PipesModule {}
