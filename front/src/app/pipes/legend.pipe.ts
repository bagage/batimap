import { Pipe, PipeTransform } from '@angular/core';
import { LegendService } from '../services/legend.service';

@Pipe({
    name: 'legend',
    pure: true
})
export class LegendPipe implements PipeTransform {
    constructor(private readonly legendService: LegendService) {}
    transform(value: string): string {
        return this.legendService.date2name(value);
    }
}
