import { Injectable } from "@angular/core";
import { AppConfigService } from "./app-config.service";

import { HttpClient } from "../../../node_modules/@angular/common/http";
import { Observable, of } from "rxjs";
import { ConflateCityDTO } from "../classes/conflate-city.dto";
import { CityDTO } from "../classes/city.dto";
import { LatLngBounds } from "leaflet";
import { plainToClass } from "class-transformer";
import { debounceTime, map, switchMap, tap } from "rxjs/operators";
import { LegendDTO } from "../classes/legend.dto";
import { LegendService } from "./legend.service";
import { ObsoleteCityDTO } from "../classes/obsolete-city.dto";

@Injectable({
  providedIn: "root"
})
export class BatimapService {
  private URL_CITY_DATA(insee: string): string {
    return (
      this.configService.getConfig().backendServerUrl + `cities/${insee}/josm`
    );
  }

  private URL_CITY_UPDATE(insee: string): string {
    return (
      this.configService.getConfig().backendServerUrl + `cities/${insee}/update`
    );
  }

  private URL_CITIES_BBOX(
    lonNW: number,
    latNW: number,
    lonSE: number,
    latSE: number
  ) {
    return (
      this.configService.getConfig().backendServerUrl +
      `cities/in_bbox/${lonNW}/${latNW}/${lonSE}/${latSE}`
    );
  }

  private URL_LEGEND(
    lonNW: number,
    latNW: number,
    lonSE: number,
    latSE: number
  ) {
    return (
      this.configService.getConfig().backendServerUrl +
      `legend/${lonNW}/${latNW}/${lonSE}/${latSE}`
    );
  }

  private URL_CITY_OBSOLETE() {
    return this.configService.getConfig().backendServerUrl + `cities/obsolete`;
  }

  constructor(
    private http: HttpClient,
    private legendService: LegendService,
    private configService: AppConfigService
  ) {}

  public cityData(insee: string): Observable<ConflateCityDTO> {
    return this.http
      .get<ConflateCityDTO>(this.URL_CITY_DATA(insee))
      .pipe(map(r => plainToClass(ConflateCityDTO, r)));
  }

  public citiesInBbox(bbox: LatLngBounds): Observable<CityDTO[]> {
    return this.http
      .get<CityDTO[]>(
        this.URL_CITIES_BBOX(
          bbox.getNorthWest().wrap().lng,
          bbox.getNorthWest().wrap().lat,
          bbox.getSouthEast().wrap().lng,
          bbox.getSouthEast().wrap().lat
        )
      )
      .pipe(
        map(r => plainToClass(CityDTO, r)),
        debounceTime(3000)
      );
  }

  public legendForBbox(bbox: LatLngBounds): Observable<LegendDTO[]> {
    return this.http
      .get<LegendDTO[]>(
        this.URL_LEGEND(
          bbox.getNorthWest().wrap().lng,
          bbox.getNorthWest().wrap().lat,
          bbox.getSouthEast().wrap().lng,
          bbox.getSouthEast().wrap().lat
        )
      )
      .pipe(
        map(r => plainToClass(LegendDTO, r)),
        switchMap((legends: LegendDTO[]) => {
          for (const l of legends) {
            l.checked = this.legendService.isActive(l);
          }
          return of(legends);
        }),
        debounceTime(3000)
      );
  }

  public updateCity(insee: string): Observable<CityDTO> {
    return this.http
      .post<CityDTO>(this.URL_CITY_UPDATE(insee), null)
      .pipe(
        tap(city => this.legendService.city2date.set(city.insee, city.date))
      );
  }

  public obsoleteCity(): Observable<ObsoleteCityDTO> {
    return this.http.get<ObsoleteCityDTO>(this.URL_CITY_OBSOLETE());
  }
}
