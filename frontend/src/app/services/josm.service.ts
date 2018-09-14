import {Injectable} from '@angular/core';
import {HttpClient} from '@angular/common/http';
import {Observable, of} from 'rxjs';
import {CityDTO} from '../classes/city.dto';
import {catchError, flatMap, map, share} from 'rxjs/operators';
import {BatimapService} from './batimap.service';

@Injectable({
  providedIn: 'root'
})
export class JosmService {
  private JOSM_URL_BASE = 'http://127.0.0.1:8111/';
  private JOSM_URL_VERSION = this.JOSM_URL_BASE + 'version';

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


  constructor(private http: HttpClient, private batimapService: BatimapService) {
  }

  public isStarted(): Observable<boolean> {
    return this.http.get(this.JOSM_URL_VERSION).pipe(map(() => true), catchError(() => of(false)), share());
  }

  public conflateCity(city: CityDTO): Observable<any> {
    // get city data
    return this.batimapService.cityData(city.insee)
      .pipe(flatMap(dto => this.JOSM_URL_IMAGERY('BDOrtho IGN', 'http://proxy-ign.openstreetmap.fr/bdortho/{z}/{x}/{y}.jpg')
        .pipe(flatMap(() => this.JOSM_URL_OPEN_FILE(dto.buildingsUrl, false)
          .pipe(flatMap(() => this.JOSM_URL_OPEN_FILE(dto.segmententationPredictionssUrl, false/*cannot be locked otherwise todo plugin wont work*/)
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
