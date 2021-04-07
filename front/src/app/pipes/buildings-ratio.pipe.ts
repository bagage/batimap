import { Pipe, PipeTransform } from '@angular/core';
import { CityDTO } from '../classes/city.dto';

@Pipe({
    name: 'buildingsratio',
})
export class BuildingsRatioPipe implements PipeTransform {
    transform(input, attribute?: string | undefined): number | string {
        let ratio: number;
        if (input instanceof CityDTO || input.osm_buildings) {
            if (!Number.isInteger(input.osm_buildings) || !Number.isInteger(input.od_buildings)) {
                return undefined;
            }

            // tslint:disable-next-line:binary-expression-operand-order
            ratio = +(100 * (1 - input.od_buildings / input.osm_buildings)).toFixed(2);
        } else {
            ratio = input;
        }

        if (attribute === 'color') {
            if (Math.abs(ratio) < 5) {
                return 'green';
            } else if (Math.abs(ratio) < 20) {
                return 'orange';
            }

            return 'red';
        } else {
            return ratio;
        }
    }
}
