import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { EMPTY, forkJoin, Observable, of } from 'rxjs';
import { catchError, map, share, switchMap } from 'rxjs/operators';
import { CityDTO } from '../classes/city.dto';
import { ConflateCityDTO } from '../classes/conflate-city.dto';
import { HttpErrorInterceptor } from './http-error.interceptor';

@Injectable({
    providedIn: 'root',
})
export class JosmService {
    private readonly JOSM_URL_BASE = 'http://127.0.0.1:8111/';
    private readonly JOSM_URL_VERSION = `${this.JOSM_URL_BASE}version`;

    constructor(private readonly http: HttpClient) {}

    isStarted(): Observable<boolean> {
        return this.http.get(this.JOSM_URL_VERSION, HttpErrorInterceptor.ByPassInterceptor()).pipe(
            map(() => true),
            catchError(() => of(false)),
            share()
        );
    }

    getOsmLayer(city: CityDTO): string {
        return `Données OSM pour ${city.insee} - ${city.name}`;
    }

    openCityInJosm(city: CityDTO, osmID: number, dto: ConflateCityDTO): Observable<any> {
        if (!dto) {
            console.log(`Asked to open ${city.name} in JOSM, but no data. Ignoring`);

            return EMPTY;
        }
        const imagery$ = this.josmUrlImageryBdortho$();
        const buildings$ = this.josmUrlImport$(dto.buildingsUrl, true, false, "never");
        const segmented$ = this.josmUrlImport$(
            dto.segmententationPredictionssUrl,
            true,
            false, // cannot be locked otherwise todo plugin wont work
            "never"
        );

        // for OSM data first we create the layer, then we try to load data
        // cf https://gitlab.com/bagage/batimap/-/issues/70
        const osm$ = this.josmUrlLoadObject$(`r${osmID}`, this.getOsmLayer(city)).pipe(
            switchMap(() =>
                this.josmUrlLoadAndZoom$(
                    false,
                    undefined,
                    dto.bbox[0].toString(),
                    dto.bbox[1].toString(),
                    dto.bbox[2].toString(),
                    dto.bbox[3].toString()
                )
            )
        );

        return forkJoin([imagery$, segmented$, buildings$]).pipe(switchMap(() => osm$));
    }

    openNodes(nodes: number[], insee: string, name: string): Observable<any> {
        const n = `n${nodes.join(',n')}`;
        const plural = nodes.length > 1 ? 's' : '';

        return forkJoin([
            this.josmUrlImageryBdortho$(),
            this.josmUrlLoadObject$(
                n,
                `Bâtiment${plural} simplifié${plural} dans ${insee} - ${name} (${nodes.join(', ')})`
            ),
        ]);
    }

    josmUrlImport$(url: string, checkExists: boolean, locked: boolean, uploadPolicy: string, layerName?: string): Observable<string> {
        // first ensure that the file exists, then load it into JOSM
        return (checkExists ? this.http.head(url, HttpErrorInterceptor.ByPassInterceptor()) : of(true)).pipe(
            catchError(e => {
                console.warn('OSM data at url', url, 'could not be found, not opening it in JOSM', e);

                return of('no segmentation');
            }),
            switchMap(a => {
                if (a === 'no segmentation') {
                    return of('no segmentation');
                }

                const params: any = {
                    new_layer: layerName === undefined ? 'true' : 'false',
                    upload_policy: uploadPolicy,
                    layer_locked: `${locked}`,
                };
                if (layerName) {
                    params.layer_name = layerName;
                }
                params.url = url;

                return this.http.get(`${this.JOSM_URL_BASE}import`, {
                    responseType: 'text',
                    params,
                });
            })
        );
    }

    private josmUrlImageryBdortho$(): Observable<string> {
        const title = 'BDOrtho IGN';
        const url = 'http://proxy-ign.openstreetmap.fr/bdortho/{z}/{x}/{y}.jpg';

        return this.http.get(`${this.JOSM_URL_BASE}imagery`, {
            responseType: 'text',
            params: {
                title,
                type: 'tms',
                url,
            },
        });
    }

    private josmUrlLoadAndZoom$(
        newLayer: boolean,
        layerName: string,
        left: string,
        right: string,
        bottom: string,
        top: string
    ): Observable<string> {
        return this.http.get(`${this.JOSM_URL_BASE}load_and_zoom`, {
            headers: HttpErrorInterceptor.ByPassInterceptor().headers,
            responseType: 'text',
            params: {
                new_layer: newLayer ? 'true' : 'false',
                layer_name: newLayer ? layerName : undefined, // unsupported
                left,
                right,
                bottom,
                top,
            },
        });
    }

    private josmUrlLoadObject$(objects: string, layerName: string): Observable<any> {
        return this.http.get(`${this.JOSM_URL_BASE}load_object`, {
            responseType: 'text',
            params: {
                new_layer: 'true',
                objects,
                layer_name: layerName,
            },
        });
    }
}
