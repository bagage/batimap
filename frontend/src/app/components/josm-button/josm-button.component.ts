import {
    ChangeDetectionStrategy,
    ChangeDetectorRef,
    Component,
    EventEmitter,
    HostListener,
    Input,
    Output
} from '@angular/core';
import { Observable, of } from 'rxjs';
import { filter, map, switchMap } from 'rxjs/operators';
import { CityDTO } from '../../classes/city.dto';
import { ConflateCityDTO } from '../../classes/conflate-city.dto';
import { Unsubscriber } from '../../classes/unsubscriber';
import {
    BatimapService,
    TaskProgress,
    TaskState
} from '../../services/batimap.service';
import { JosmService } from '../../services/josm.service';

@Component({
    selector: 'app-josm-button',
    changeDetection: ChangeDetectionStrategy.OnPush,
    templateUrl: './josm-button.component.html',
    styleUrls: ['./josm-button.component.css']
})
export class JosmButtonComponent extends Unsubscriber {
    @Input()
    set city(value: CityDTO) {
        this._city = value;
        if (value.josm_ready) {
            this.options.tooltip =
                'Ouvre JOSM avec les calques préconfigurés pour la commune sélectionnée. ' +
                "Si le bouton n'est pas actif, JOSM n'est probablement pas démarré. [Raccourci : J]";
            this.options.text = 'JOSM';
            this.options.barColor = this.options.buttonColor = 'primary';
        } else {
            this.options.tooltip =
                'Prépare les données pour pouvoir être ensuite éditer avec JOSM. [Raccourci : P]';
            this.options.text = 'Préparer';
            this.options.barColor = this.options.buttonColor = 'secondary';
        }
    }

    @Input()
    set josmReady(value: boolean) {
        this.options.disabled = this._city.josm_ready && !value;
    }

    @Output() readonly newestDate = new EventEmitter<string>();

    options = {
        active: false,
        text: '',
        buttonColor: 'primary',
        barColor: 'primary',
        raised: true,
        stroked: false,
        mode: 'indeterminate',
        value: 0,
        disabled: false,
        tooltip: ''
    };
    private _city: CityDTO;

    constructor(
        private readonly josmService: JosmService,
        private readonly batimapService: BatimapService,
        private readonly changeDetector: ChangeDetectorRef
    ) {
        super();
    }

    @HostListener('document:keydown.j') onClick() {
        this.options.active = true;
        const obs = this._city.josm_ready
            ? this.conflateCity()
            : this.prepareCity();
        this.autoUnsubscribe(
            obs.subscribe(
                progress => {
                    if (progress && progress.current !== undefined) {
                        const prog = ` (${progress.current}%)`;
                        if (this.options.text.indexOf('(') === -1) {
                            this.options.text += prog;
                        } else {
                            this.options.text = this.options.text.replace(
                                / \(.*\)/,
                                prog
                            );
                        }
                        this.changeDetector.detectChanges();
                    }
                },
                undefined,
                () => {
                    this.options.active = false;
                    this.options.text = this.options.text.replace(
                        / \(.*\)/,
                        ''
                    );
                    this.changeDetector.detectChanges();
                }
            )
        );
    }

    private conflateCity(): Observable<any> {
        return this.prepareCity().pipe(
            switchMap(dto =>
                dto instanceof TaskProgress
                    ? of(dto)
                    : this.josmService.openCityInJosm(this._city, dto)
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
                        this.newestDate.emit(progressConflateDTO.date);

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
