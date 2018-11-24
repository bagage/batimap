import {Type} from 'class-transformer';
import {CityDetailsDTO} from './city-details.dto';

export class CityDTO {
  name: string;
  @Type(() => CityDetailsDTO)
  details: CityDetailsDTO;
  date: string; // date of latest cadastral import, or unknown, or never
  insee: string;
  @Type(() => Boolean)
  josm_ready: boolean;
}
