import { Type } from 'class-transformer';

export class CityDTO {
    name: string;
    @Type(() => CityDetailsDTO)
    details: CityDetailsDTO; // number of buildings imported per year date
    date: string; // date of latest cadastral import, or unknown, or never
    insee: string;
    @Type(() => Boolean)
    josm_ready: boolean;
}

export class CityDetailsDTO {
    @Type(() => Number)
    dates: Map<string, number>;
    simplified: number[];
}
