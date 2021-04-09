import { Pipe, PipeTransform } from '@angular/core';
import { CityDTO } from '../classes/city.dto';

@Pipe({
    name: 'buildingsratio',
})
export class BuildingsRatioPipe implements PipeTransform {
    greenPercentage = 20;
    orangePercentage = 50;

    transform(input: any, attribute?: string | undefined): number | string | undefined {
        let ratio: number;
        if (input instanceof CityDTO || input.osm_buildings !== undefined) {
            if (!Number.isInteger(input.osm_buildings) || !Number.isInteger(input.od_buildings)) {
                return undefined;
            }

            // eslint-disable-next-line yoda
            ratio = +(100 * (1 - input.od_buildings / input.osm_buildings)).toFixed(2);
        } else {
            ratio = input;
        }

        /* do not forget to update map-date-legend.component.css if colors are modified */
        if (attribute === 'color') {
            if (Math.abs(ratio) < this.greenPercentage) {
                return 'green';
            } else if (Math.abs(ratio) < this.orangePercentage) {
                return 'orange';
            }

            return 'red';
        } else {
            return ratio;
        }
    }
}
