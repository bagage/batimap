import { Pipe, PipeTransform } from '@angular/core';
import { CityDTO } from '../classes/city.dto';

@Pipe({
    name: 'buildingsratio',
})
export class BuildingsRatioPipe implements PipeTransform {
    transform(city: CityDTO, attribute?: string | undefined): number | string {
        if (city.osm_buildings === undefined || city.od_buildings === undefined) {
            return undefined;
        }

        // tslint:disable-next-line:binary-expression-operand-order
        const ratio = +(100 * (1 - city.od_buildings / city.osm_buildings)).toFixed(2);

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
