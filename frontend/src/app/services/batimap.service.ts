import {Injectable} from "@angular/core";
import {AppConfigService} from "./app-config.service";

import {HttpClient} from "../../../node_modules/@angular/common/http";
import {Observable, of, timer} from "rxjs";
import {ConflateCityDTO} from "../classes/conflate-city.dto";
import {CityDTO} from "../classes/city.dto";
import {LatLngBounds} from "leaflet";
import {plainToClass} from "class-transformer";
import {debounceTime, map, switchMap, takeWhile, tap} from "rxjs/operators";
import {LegendDTO} from "../classes/legend.dto";
import {LegendService} from "./legend.service";
import {ObsoleteCityDTO} from "../classes/obsolete-city.dto";
import {ClassType} from "../../../node_modules/class-transformer/ClassTransformer";

export interface Progression<T> {
  state: string;
  result: T;
}

export interface Task {
  task_id: string;
}

@Injectable({
  providedIn: "root"
})
export class BatimapService {
  private URL_TASK(task: Task): string {
    return (
      this.configService.getConfig().backendServerUrl + `/tasks/${task.task_id}`
    );
  }

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
  ) {
  }

  private longRunningAPI<T>(
    url,
    cls: ClassType<T>
  ): Observable<Progression<T>> {
    let hasFinished = false;
    return this.http.get<Task>(url).pipe(
      switchMap(task =>
        timer(0, 3000).pipe(
          switchMap(() => this.http.get<Progression<T>>(this.URL_TASK(task))),
          // takeWhile is not inclusive, so workaround it with a boolean cf https://github.com/ReactiveX/rxjs/issues/4000
          takeWhile(x => x.state === "PENDING" || x.state === "PROGRESS" || !hasFinished),
          tap(x => (hasFinished = x.state !== "PENDING" && x.state !== "PROGRESS")),
          map(r => {
            r.result = plainToClass(cls, r.result);
            return r;
          })
        )
      )
    );
  }

  public cityData(insee: string): Observable<Progression<ConflateCityDTO>> {
    return this.longRunningAPI<ConflateCityDTO>(
      this.URL_CITY_DATA(insee),
      ConflateCityDTO
    );
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

  public updateCity(insee: string): Observable<Progression<CityDTO>> {
    return this.longRunningAPI<CityDTO>(
      this.URL_CITY_UPDATE(insee),
      CityDTO
    ).pipe(
      tap(progress => {
        if (progress.result) {
          this.legendService.city2date.set(
            progress.result.insee,
            progress.result.date
          );
        }
      })
    );
  }

  public obsoleteCity(ignored: string[]): Observable<ObsoleteCityDTO> {
    return this.http.get<ObsoleteCityDTO>(this.URL_CITY_OBSOLETE(),
      {
        params: {
          ignored: ignored.join(',')
        }
      });
  }
}
