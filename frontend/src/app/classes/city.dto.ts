import {Type} from 'class-transformer';

export class CityDTO {
  name: string;
  details: any; // number of buildings imported per year date
  date: string; // date of latest cadastral import, or unknown, or never
  insee: string;
  @Type(() => Boolean)
  josm_ready: boolean;
}
