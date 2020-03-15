import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { EMPTY, forkJoin, Observable, of } from 'rxjs';
import { catchError, map, share, switchMap } from 'rxjs/operators';
import { CityDTO } from '../classes/city.dto';
import { ConflateCityDTO } from '../classes/conflate-city.dto';

@Injectable({
    providedIn: 'root'
})
export class JosmService {
    private readonly JOSM_URL_BASE = 'http://127.0.0.1:8111/';
    private readonly JOSM_URL_VERSION = `${this.JOSM_URL_BASE}version`;

    constructor(private readonly http: HttpClient) {}

    isStarted(): Observable<boolean> {
        return this.http.get(this.JOSM_URL_VERSION).pipe(
            map(() => true),
            catchError(() => of(false)),
            share()
        );
    }

    openCityInJosm(city: CityDTO, dto: ConflateCityDTO): Observable<any> {
        if (!dto) {
            console.log(`Asked to open ${city.name} in JOSM, but no data. Ignoring`);

            return EMPTY;
        }
        const imagery = this.JOSM_URL_BDORTHO_IMAGERY();
        const buildings = this.JOSM_URL_OPEN_FILE(dto.buildingsUrl, false);
        const segmented = this.JOSM_URL_OPEN_FILE(
            dto.segmententationPredictionssUrl,
            false // cannot be locked otherwise todo plugin wont work
        );
        const osm = this.JOSM_URL_OSM_DATA_FOR_BBOX(
            `Données OSM pour ${city.insee} - ${city.name}`,
            dto.bbox[0].toString(),
            dto.bbox[1].toString(),
            dto.bbox[2].toString(),
            dto.bbox[3].toString()
        );

        return forkJoin(imagery, buildings, segmented, osm);
    }

    openNode(node: number, city: CityDTO): Observable<any> {
        return forkJoin(
            this.JOSM_URL_BDORTHO_IMAGERY(),
            this.JOSM_URL_LOAD_OBJECTS(`n${node}`, `Bâtiment simplifié ${node} dans ${city.insee} - ${city.name}`)
        );
    }

    private JOSM_URL_BDORTHO_IMAGERY(): Observable<string> {
        const title = 'BDOrtho IGN';
        const url = 'http://proxy-ign.openstreetmap.fr/bdortho/{z}/{x}/{y}.jpg';

        return this.http.get(`${this.JOSM_URL_BASE}imagery`, {
            responseType: 'text',
            params: {
                title,
                type: 'tms',
                url
            }
        });
    }

    private JOSM_URL_OPEN_FILE(url: string, locked: boolean): Observable<string> {
        // first ensure that the file exists, then load it into JOSM
        return this.http.head(url).pipe(
            catchError(e => {
                console.warn('OSM data at url', url, 'could not be found, not opening it in JOSM', e);

                return of('no segmentation');
            }),
            switchMap(a => {
                if (a !== 'no segmentation') {
                    return this.http.get(`${this.JOSM_URL_BASE}import`, {
                        responseType: 'text',
                        params: {
                            new_layer: 'true',
                            upload_policy: locked ? 'never' : 'true',
                            layer_locked: `${locked}`,
                            url
                        }
                    });
                }

                return of('no segmentation');
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
        return this.http.get(`${this.JOSM_URL_BASE}load_and_zoom`, {
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

    private JOSM_URL_LOAD_OBJECTS(objects: string, layerName: string): Observable<any> {
        return this.http.get(`${this.JOSM_URL_BASE}load_object`, {
            responseType: 'text',
            params: {
                new_layer: 'true',
                objects,
                layer_name: layerName
            }
        });
    }
}
