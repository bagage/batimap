import { Injectable } from '@angular/core';
import { AppConfigService } from './app-config.service';

import { plainToClass } from 'class-transformer';
import { LatLngBounds } from 'leaflet';
import { Observable, of, timer } from 'rxjs';
import { debounceTime, map, switchMap, takeWhile, tap } from 'rxjs/operators';
import { HttpClient } from '../../../node_modules/@angular/common/http';
import { ClassType } from '../../../node_modules/class-transformer/ClassTransformer';
import { CityDTO } from '../classes/city.dto';
import { ConflateCityDTO } from '../classes/conflate-city.dto';
import { LegendDTO } from '../classes/legend.dto';
import { ObsoleteCityDTO } from '../classes/obsolete-city.dto';
import { LegendService } from './legend.service';

export enum TaskState {
    PENDING = 'PENDING',
    PROGRESS = 'PROGRESS',
    FAILURE = 'FAILURE',
    SUCCESS = 'SUCCESS'
}

export interface TaskResult<T> {
    state: TaskState;
    result: T;
    progress: TaskProgress;
}

export interface Task {
    task_id: string;
}

export class TaskProgress {
    constructor(public current: number, public total: number) {}
}

@Injectable({
    providedIn: 'root'
})
export class BatimapService {
    constructor(
        private readonly http: HttpClient,
        private readonly legendService: LegendService,
        private readonly configService: AppConfigService
    ) {}

    cityData(insee: string): Observable<TaskResult<ConflateCityDTO>> {
        return this.longRunningAPI<ConflateCityDTO>(
            this.URL_CITY_DATA(insee),
            ConflateCityDTO
        );
    }

    citiesInBbox(bbox: LatLngBounds): Observable<CityDTO[]> {
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

    legendForBbox(bbox: LatLngBounds): Observable<LegendDTO[]> {
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

    updateCity(insee: string): Observable<TaskResult<CityDTO>> {
        return this.longRunningAPI<CityDTO>(
            this.URL_CITY_UPDATE(insee),
            CityDTO
        ).pipe(
            tap(progress => {
                if (progress.state === TaskState.SUCCESS) {
                    this.legendService.city2date.set(
                        progress.result.insee,
                        progress.result.date
                    );
                }
            })
        );
    }

    obsoleteCity(ignored: string[]): Observable<ObsoleteCityDTO> {
        return this.http.get<ObsoleteCityDTO>(this.URL_CITY_OBSOLETE(), {
            params: {
                ignored: ignored.join(',')
            }
        });
    }
    private URL_TASK(task: Task): string {
        return `${this.configService.getConfig().backendServerUrl}/tasks/${
            task.task_id
        }`;
    }

    private URL_CITY_DATA(insee: string): string {
        return `${
            this.configService.getConfig().backendServerUrl
        }cities/${insee}/josm`;
    }

    private URL_CITY_UPDATE(insee: string): string {
        return `${
            this.configService.getConfig().backendServerUrl
        }cities/${insee}/update`;
    }

    private URL_CITIES_BBOX(
        lonNW: number,
        latNW: number,
        lonSE: number,
        latSE: number
    ) {
        return `${
            this.configService.getConfig().backendServerUrl
        }cities/in_bbox/${lonNW}/${latNW}/${lonSE}/${latSE}`;
    }

    private URL_LEGEND(
        lonNW: number,
        latNW: number,
        lonSE: number,
        latSE: number
    ) {
        return `${
            this.configService.getConfig().backendServerUrl
        }legend/${lonNW}/${latNW}/${lonSE}/${latSE}`;
    }

    private URL_CITY_OBSOLETE() {
        return `${
            this.configService.getConfig().backendServerUrl
        }cities/obsolete`;
    }

    private longRunningAPI<T>(
        url,
        cls: ClassType<T>
    ): Observable<TaskResult<T>> {
        return this.http.get<Task>(url).pipe(
            switchMap(task =>
                timer(0, 3000).pipe(
                    switchMap(() =>
                        this.http.get<TaskResult<T>>(this.URL_TASK(task))
                    ),
                    takeWhile(
                        r =>
                            r.state === TaskState.PENDING ||
                            r.state === TaskState.PROGRESS,
                        true
                    ),
                    tap(r => {
                        if (r.state === TaskState.PENDING) {
                            r.progress = new TaskProgress(0, 100);
                        } else if (r.state === TaskState.PROGRESS) {
                            r.progress = plainToClass(TaskProgress, r.result);
                            r.result = undefined;
                        } else if (r.state === TaskState.FAILURE) {
                            throw new Error(r.result.toString());
                        } else {
                            r.result = plainToClass(cls, r.result);
                            r.progress = new TaskProgress(100, 100);
                        }
                    })
                )
            )
        );
    }
}
