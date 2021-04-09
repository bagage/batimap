import { Type } from 'class-transformer';
import { CityDTO } from './city.dto';

export class ObsoleteCityDTO {
    position!: [number, number];
    osmid!: number;

    @Type(() => CityDTO) city!: CityDTO;
}
