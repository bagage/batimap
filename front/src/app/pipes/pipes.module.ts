import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { CountPipe } from './count.pipe';
import { LegendPipe } from './legend.pipe';

@NgModule({
    declarations: [CountPipe, LegendPipe],
    exports: [CountPipe, LegendPipe],
    imports: [CommonModule]
})
export class PipesModule {}
