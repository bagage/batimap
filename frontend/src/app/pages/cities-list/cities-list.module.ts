import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { SharedComponentsModule } from '../../components/shared-components.module';
import { MatLibModule } from '../../mat-lib.module';
import { CitiesListComponent } from './cities-list.component';

@NgModule({
    imports: [CommonModule, MatLibModule, SharedComponentsModule],
    declarations: [CitiesListComponent],
    exports: [CitiesListComponent]
})
export class CitiesListModule {}
