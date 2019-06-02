import { Type } from 'class-transformer';

export class CityDetailsDTO {
    @Type(() => Number) dates: Map<string, number>;
    simplified: Array<number>;
}

export class CityDTO {
    name: string;
    @Type(() => CityDetailsDTO) details: CityDetailsDTO; // number of buildings imported per year date
    date: string; // date of latest cadastral import, or unknown, or never
    insee: string;
    // tslint:disable-next-line:variable-name
    @Type(() => Boolean) josm_ready: boolean;
}
