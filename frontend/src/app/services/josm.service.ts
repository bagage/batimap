import { Injectable } from "@angular/core";
import { HttpClient } from "@angular/common/http";
import { empty, forkJoin, Observable, of } from "rxjs";
import { CityDTO } from "../classes/city.dto";
import {
  catchError, filter,
  flatMap,
  map,
  share,
  switchMap,
  tap
} from 'rxjs/operators';
import { BatimapService } from "./batimap.service";

@Injectable({
  providedIn: "root"
})
export class JosmService {
  private JOSM_URL_BASE = "http://127.0.0.1:8111/";
  private JOSM_URL_VERSION = this.JOSM_URL_BASE + "version";

  private JOSM_URL_IMAGERY(title: string, url: string): Observable<string> {
    return this.http.get(this.JOSM_URL_BASE + "imagery", {
      responseType: "text",
      params: {
        title,
        type: "tms",
        url
      }
    });
  }

  private JOSM_URL_OPEN_FILE(url: string, locked: boolean): Observable<string> {
    // first ensure that the file exists, then load it into JOSM
    return this.http.head(url).pipe(
      catchError(e => {
        console.warn(
          "OSM data at url",
          url,
          "could not be found, not opening it in JOSM",
          e
        );
        return of("no segmentation");
      }),
      switchMap(a => {
        if (a !== "no segmentation") {
          return this.http.get(this.JOSM_URL_BASE + "import", {
            responseType: "text",
            params: {
              new_layer: "true",
              upload_policy: locked ? "never" : "true",
              layer_locked: `${locked}`,
              url
            }
          });
        } else {
          return of("no segmentation");
        }
      })
    );
  }

  private JOSM_URL_OSM_DATA_FOR_BBOX(
    layerName: string,
    left: string,
    right: string,
    bottom: string,
    top: string
  ): Observable<string> {
    return this.http.get(this.JOSM_URL_BASE + "load_and_zoom", {
      responseType: "text",
      params: {
        new_layer: "true",
        layer_name: layerName,
        left,
        right,
        bottom,
        top
      }
    });
  }

  constructor(
    private http: HttpClient,
    private batimapService: BatimapService
  ) {}

  public isStarted(): Observable<boolean> {
    return this.http.get(this.JOSM_URL_VERSION).pipe(
      map(() => true),
      catchError(() => of(false)),
      share()
    );
  }

  public conflateCity(city: CityDTO): Observable<any> {
    // get city data
    return this.batimapService.cityData(city.insee).pipe(
      filter(progress => progress.result !== null),
      flatMap(progress => {
        const dto = progress.result;
        const imagery = this.JOSM_URL_IMAGERY(
          "BDOrtho IGN",
          "http://proxy-ign.openstreetmap.fr/bdortho/{z}/{x}/{y}.jpg"
        );
        const buildings = this.JOSM_URL_OPEN_FILE(dto.buildingsUrl, false);
        const segmented = this.JOSM_URL_OPEN_FILE(
          dto.segmententationPredictionssUrl,
          false /*cannot be locked otherwise todo plugin wont work*/
        );
        const osm = this.JOSM_URL_OSM_DATA_FOR_BBOX(
          `Données OSM pour ${city.insee} - ${city.name}`,
          dto.bbox[0].toString(),
          dto.bbox[1].toString(),
          dto.bbox[2].toString(),
          dto.bbox[3].toString()
        );
        return forkJoin(imagery, buildings, segmented, osm);
      })
    );
  }
}
