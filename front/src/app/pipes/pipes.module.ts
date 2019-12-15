import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { CountPipe } from './count.pipe';

@NgModule({
    declarations: [CountPipe],
    exports: [CountPipe],
    imports: [CommonModule]
})
export class PipesModule {}
