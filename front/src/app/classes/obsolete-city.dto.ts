import { CityDTO } from './city.dto';
import { Type } from 'class-transformer';

export class ObsoleteCityDTO {
    @Type(() => CityDTO) city!: CityDTO;
    position!: [number, number];
    osmid!: number;
}
