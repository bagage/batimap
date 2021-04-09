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
    // eslint-disable-next-line @typescript-eslint/naming-convention,no-underscore-dangle,id-blacklist,id-match
    @Type(() => Boolean) josm_ready!: boolean;
    // eslint-disable-next-line @typescript-eslint/naming-convention,no-underscore-dangle,id-blacklist,id-match
    osm_buildings!: number;
    // eslint-disable-next-line @typescript-eslint/naming-convention, no-underscore-dangle, id-blacklist, id-match
    od_buildings!: number;
}
