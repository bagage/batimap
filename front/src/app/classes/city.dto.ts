import { Type } from 'class-transformer';

export class StatsDetailsDTO {
    @Type() dates!: Map<string, number>;
    simplified!: number[];
}

export class CityDTO {
    name!: string;
    @Type(() => StatsDetailsDTO) details?: StatsDetailsDTO; // number of buildings imported per year
    date!: string; // date of latest cadastral import, or unknown, or never
    insee!: string;
    // tslint:disable-next-line:variable-name
    @Type(() => Boolean) josm_ready!: boolean;
    // tslint:disable-next-line:variable-name
    osm_buildings!: number;
    // tslint:disable-next-line:variable-name
    od_buildings!: number;
}
