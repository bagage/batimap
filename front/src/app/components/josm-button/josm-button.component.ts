import {
    ChangeDetectionStrategy,
    ChangeDetectorRef,
    Component,
    EventEmitter,
    HostListener,
    Input,
    OnInit,
    Output,
} from '@angular/core';
import { MatProgressButtonOptions } from 'mat-progress-buttons';
import { EMPTY, Observable, of } from 'rxjs';
import { map, switchMap } from 'rxjs/operators';
import { CityDTO } from '../../classes/city.dto';
import { ConflateCityDTO } from '../../classes/conflate-city.dto';
import { BatimapService, TaskProgress, TaskState } from '../../services/batimap.service';
import { JosmService } from '../../services/josm.service';
import { Unsubscriber } from '../unsubscriber';

@Component({
    selector: 'app-josm-button',
    changeDetection: ChangeDetectionStrategy.OnPush,
    templateUrl: './josm-button.component.html',
    styleUrls: ['./josm-button.component.css'],
})
export class JosmButtonComponent extends Unsubscriber implements OnInit {
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

    @Input() osmID!: number;
    /* eslint-disable @typescript-eslint/naming-convention, no-underscore-dangle, id-blacklist, id-match */
    private _city!: CityDTO;
    @Input()
    set city(value: CityDTO) {
        const changed = value && this._city && this._city.insee !== value.insee;
        const isRaster = value.date === 'raster';
        this._city = value;
        if (isRaster) {
            this.options.disabled = true;
            this.tooltip = "Commune raster, pas d'import possible.";
            this.options.text = 'JOSM';
        } else if (value.josm_ready) {
            this.tooltip =
                'Ouvre JOSM avec les calques préconfigurés pour la commune sélectionnée. ' +
                "Si le bouton n'est pas actif, JOSM n'est probablement pas démarré. [Raccourci : J]";
            this.options.text = 'JOSM';
            this.options.barColor = this.options.buttonColor = 'primary';
        } else {
            this.tooltip = 'Prépare les données pour pouvoir être ensuite éditer avec JOSM. [Raccourci : P]';
            this.options.text = 'Préparer';
            this.options.barColor = this.options.buttonColor = 'accent';

            if (changed) {
                this.checkIsPreparing();
            }
        }
    }

    @Input()
    set josmReady(ready: boolean | null) {
        // button must be disabled:
        // 1. completely for raster city
        // 2. only if city data are available but JOSM is not available
        this.options.disabled = this._city.date === 'raster' || (this._city.josm_ready && !ready);
    }

    constructor(
        private readonly josmService: JosmService,
        private readonly batimapService: BatimapService,
        private readonly changeDetector: ChangeDetectorRef
    ) {
        super();
    }

    ngOnInit(): void {
        if (this._city) {
            this.checkIsPreparing();
        }
    }

    checkIsPreparing(): void {
        // check if the current city
        this.options.active = true;
        this.autoUnsubscribe(
            this.batimapService.cityTasks(this._city.insee).subscribe(tasks => {
                if (tasks.length) {
                    this.onClick();
                } else {
                    this.options.active = false;
                    this.options.text = this.options.text.replace(/ \(.*\)/, '');
                    this.changeDetector.detectChanges();
                }
            })
        );
    }

    @HostListener('document:keydown.j') onClick(): void {
        this.options.active = true;
        const onEnd = () => {
            this.options.active = false;
            this.options.text = this.options.text.replace(/ \(.*\)/, '');
            this.changeDetector.detectChanges();
        };

        const obs$ = this._city.josm_ready ? this.conflateCity() : this.prepareCity();

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
                dto instanceof TaskProgress
                    ? of(dto)
                    : dto
                    ? this.josmService.openCityInJosm(this._city, this.osmID, dto)
                    : EMPTY
            )
        );
    }

    private prepareCity(): Observable<ConflateCityDTO | TaskProgress | undefined> {
        return this.batimapService.cityData(this._city.insee).pipe(
            map(task => {
                if (task.state === TaskState.SUCCESS) {
                    if (task.result) {
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
                    }
                    throw Error('unexpected state');
                } else {
                    return task.progress;
                }
            })
        );
    }
}
