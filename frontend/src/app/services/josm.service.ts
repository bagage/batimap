import {Injectable} from '@angular/core';
import {HttpClient, HttpHeaders} from '@angular/common/http';
import {forkJoin, Observable} from 'rxjs';
import {City} from '../classes/city';
import {flatMap, map} from 'rxjs/operators';
import {environment} from '../../environments/environment';

class ConflateCityDTO {
  buildingsUrl: string;
  segmententationPredictionssUrl: string;
  bbox: [number, number, number, number];
}

@Injectable({
  providedIn: 'root'
})
export class JosmService {
  private JOSM_URL_BASE = 'http://127.0.0.1:8111/';
  private JOSM_URL_VERSION = this.JOSM_URL_BASE + 'version';

  private URL_CITY_DATA(insee: string): string {
    return environment.serverUrl + 'josm/' + insee;
  }

  private JOSM_URL_IMAGERY(title: string, url: string): Observable<any> {
    return this.http.get(this.JOSM_URL_BASE + 'imagery', {
      responseType: 'text',
      params: {
        title,
        type: 'tms',
        url
      }
    });
  };

  private JOSM_URL_OPEN_FILE(url: string, locked: boolean): Observable<any> {
    return this.http.get(this.JOSM_URL_BASE + 'import', {
      responseType: 'text',
      params: {
        new_layer: 'true',
        upload_policy: locked ? 'never' : 'true',
        layer_locked: `${locked}`,
        url
      }
    });
  };

  private JOSM_URL_OSM_DATA_FOR_BBOX(layerName: string, left: string, right: string, bottom: string, top: string): Observable<any> {
    return this.http.get(this.JOSM_URL_BASE + 'load_and_zoom',
      {
        responseType: 'text',
        params: {
          new_layer: 'true',
          layer_name: layerName,
          left,
          right,
          bottom,
          top
        }
      });
  }


  constructor(private http: HttpClient) {
  }

  public isStarted(): Observable<any> {
    return this.http.get(this.JOSM_URL_VERSION);
  }

  public conflateCity(city: City): Observable<any> {
    // get city data
    return this.http.get<ConflateCityDTO>(this.URL_CITY_DATA(city.insee))
      .pipe(flatMap(dto => this.JOSM_URL_IMAGERY('BDOrtho IGN', 'http://proxy-ign.openstreetmap.fr/bdortho/{z}/{x}/{y}.jpg')
        .pipe(flatMap(() => this.JOSM_URL_OPEN_FILE(dto.buildingsUrl, false)
          .pipe(flatMap(() => this.JOSM_URL_OPEN_FILE(dto.segmententationPredictionssUrl, true)
            .pipe(flatMap(() => this.JOSM_URL_OSM_DATA_FOR_BBOX(`Données OSM pour ${city.insee} - ${city.name}`,
              dto.bbox[0].toString(),
              dto.bbox[1].toString(),
              dto.bbox[2].toString(),
              dto.bbox[3].toString()
            )))
          ))
        ))
      ));
  }
}
