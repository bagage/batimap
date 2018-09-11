import {Injectable} from '@angular/core';
import {environment} from '../../environments/environment';
import {HttpClient} from '../../../node_modules/@angular/common/http';
import {Observable, of, pipe} from 'rxjs';
import {ConflateCityDTO} from '../classes/conflate-city.dto';
import {CityDTO} from '../classes/city.dto';
import {LatLngBounds} from 'leaflet';
import {plainToClass} from 'class-transformer';
import {map, switchMap} from 'rxjs/operators';
import {LegendDTO} from '../classes/legend.dto';
import {LegendService} from './legend.service';

@Injectable({
  providedIn: 'root'
})
export class BatimapService {

  private URL_CITY_DATA(insee: string): string {
    return environment.backendServerUrl + 'josm/' + insee;
  }

  private URL_CITIES_BBOX(lonNW: number, latNW: number, lonSE: number, latSE: number) {
    return environment.backendServerUrl + `cities/in_bbox/${lonNW}/${latNW}/${lonSE}/${latSE}`;
  }

  private URL_LEGEND(lonNW: number, latNW: number, lonSE: number, latSE: number) {
    return environment.backendServerUrl + `legend/${lonNW}/${latNW}/${lonSE}/${latSE}`;
  }

  constructor(private http: HttpClient, private legendService: LegendService) {
  }

  public cityData(insee: string): Observable<ConflateCityDTO> {
    return this.http.get<ConflateCityDTO>(this.URL_CITY_DATA(insee)).pipe(map(r => plainToClass(ConflateCityDTO, r)));
  }

  public citiesInBbox(bbox: LatLngBounds): Observable<CityDTO[]> {
    return this.http.get<CityDTO[]>(
      this.URL_CITIES_BBOX(bbox.getNorthWest().lng, bbox.getNorthWest().lat, bbox.getSouthEast().lng, bbox.getSouthEast().lat))
      .pipe(map(r => plainToClass(CityDTO, r)));
  }

  public legendForBbox(bbox: LatLngBounds): Observable<LegendDTO[]> {
    return this.http.get<LegendDTO[]>(
      this.URL_LEGEND(bbox.getNorthWest().lng, bbox.getNorthWest().lat, bbox.getSouthEast().lng, bbox.getSouthEast().lat))
      .pipe(map(r => plainToClass(LegendDTO, r)))
      .pipe(switchMap((legends: LegendDTO[]) => {
          for (const l of legends) {
            l.checked = this.legendService.isActive(l);
          }
          return of(legends);
        }));
  }
}
