import {Type} from 'class-transformer';

export class City {
  name: string;
  @Type(() => CityDetails)
  details: CityDetails;
  date: string; // date of latest cadastral import, or unknown, or never
  insee: string;
}

export class CityDetails {
  dates: Map<string, number>; // number of buildings imported per year date
  authors: Map<string, number>; // number of buildings by OSM contributor (last edit)
}
