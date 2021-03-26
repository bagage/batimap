import {
    ChangeDetectionStrategy,
    ChangeDetectorRef,
    Component,
    EventEmitter,
    HostListener,
    Input,
    Output,
} from '@angular/core';
import { MatProgressButtonOptions } from 'mat-progress-buttons';
import { Observable, of } from 'rxjs';
import { catchError, filter, map, switchMap } from 'rxjs/operators';
import { CityDTO } from '../../classes/city.dto';
import { ConflateCityDTO } from '../../classes/conflate-city.dto';
import { Unsubscriber } from '../../classes/unsubscriber';
import { BatimapService, TaskProgress, TaskState } from '../../services/batimap.service';
import { JosmService } from '../../services/josm.service';

@Component({
    selector: 'app-josm-button',
    changeDetection: ChangeDetectionStrategy.OnPush,
    templateUrl: './josm-button.component.html',
    styleUrls: ['./josm-button.component.css'],
})
export class JosmButtonComponent extends Unsubscriber {
    @Output() readonly newerDate = new EventEmitter<CityDTO>();

    options: MatProgressButtonOptions = {
        active: false,
        text: '',
        buttonColor: 'primary',
        barColor: 'primary',
        raised: true,
        stroked: false,
        mode: 'indeterminate',
        value: 0,
        disabled: false,
    };
    tooltip = '';
    overpassAPI = 'https://overpass-api.de/api/interpreter?data=';

    @Input() osmID: number;
    private _city: CityDTO;
    @Input()
    set city(value: CityDTO) {
        this._city = value;
        if (value.josm_ready) {
            this.tooltip =
                'Ouvre JOSM avec les calques préconfigurés pour la commune sélectionnée. ' +
                "Si le bouton n'est pas actif, JOSM n'est probablement pas démarré. [Raccourci : J]";
            this.options.text = 'JOSM';
            this.options.barColor = this.options.buttonColor = 'primary';
        } else {
            this.tooltip = 'Prépare les données pour pouvoir être ensuite éditer avec JOSM. [Raccourci : P]';
            this.options.text = 'Préparer';
            this.options.barColor = this.options.buttonColor = 'accent';
        }
    }

    @Input()
    set josmReady(value: boolean) {
        this.options.disabled = this._city.josm_ready && !value;
    }

    constructor(
        private readonly josmService: JosmService,
        private readonly batimapService: BatimapService,
        private readonly changeDetector: ChangeDetectorRef
    ) {
        super();
    }

    generateOverpassQuery(name: string) {
        return `[out:xml][timeout:600];
    {{geocodeArea:"${name}, France"}}->.searchArea;
    (
    nwr(area.searchArea);
    );
    out meta; >; out meta qt;`;
    }

    @HostListener('document:keydown.j') onClick() {
        this.options.active = true;
        const onEnd = () => {
            this.options.active = false;
            this.options.text = this.options.text.replace(/ \(.*\)/, '');
            this.changeDetector.detectChanges();
        };

        const obs$ = (this._city.josm_ready ? this.conflateCity() : this.prepareCity()).pipe(
            catchError(error => {
                // use overpass query to download when city is too big for JOSM
                if (error && error.status === 502) {
                    const encodedUrl =
                        this.overpassAPI + encodeURIComponent(this.generateOverpassQuery(this._city.name));

                    return this.josmService.josmUrlImport$(
                        encodedUrl,
                        false,
                        false,
                        this.josmService.getOsmLayer(this._city)
                    );
                }

                throw error;
            })
        );

        this.autoUnsubscribe(
            obs$.subscribe(
                progress => {
                    if (progress && progress.current !== undefined) {
                        const prog = ` (${progress.current}%)`;
                        if (this.options.text.indexOf('(') === -1) {
                            this.options.text += prog;
                        } else {
                            this.options.text = this.options.text.replace(/ \(.*\)/, prog);
                        }
                        this.changeDetector.detectChanges();
                    }
                },
                onEnd,
                onEnd
            )
        );
    }

    private conflateCity(): Observable<any> {
        return this.prepareCity().pipe(
            switchMap(dto =>
                dto instanceof TaskProgress ? of(dto) : this.josmService.openCityInJosm(this._city, this.osmID, dto)
            )
        );
    }

    private prepareCity(): Observable<ConflateCityDTO | TaskProgress> {
        return this.batimapService.cityData(this._city.insee).pipe(
            map(task => {
                if (task.state === TaskState.SUCCESS) {
                    const progressConflateDTO = task.result;

                    if (progressConflateDTO.buildingsUrl) {
                        const c = this._city;
                        c.josm_ready = true;
                        this.city = c;
                    }

                    if (this._city.date !== progressConflateDTO.date) {
                        this._city.date = progressConflateDTO.date;
                        this.newerDate.emit(this._city);

                        return undefined;
                    }

                    if (progressConflateDTO.buildingsUrl) {
                        return progressConflateDTO;
                    }
                } else {
                    return task.progress;
                }
            })
        );
    }
}
