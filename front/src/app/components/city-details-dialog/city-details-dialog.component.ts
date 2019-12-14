import {
    Component,
    HostListener,
    Inject,
    OnInit,
    SimpleChanges
} from '@angular/core';
import {
    MAT_DIALOG_DATA,
    MatDialog,
    MatDialogRef
} from '@angular/material/dialog';
import { MatProgressButtonOptions } from 'mat-progress-buttons';
import { Observable } from 'rxjs';
import { CityDTO } from '../../classes/city.dto';
import { Unsubscriber } from '../../classes/unsubscriber';
import { BatimapService, TaskState } from '../../services/batimap.service';
import { JosmService } from '../../services/josm.service';
import { LegendService } from '../../services/legend.service';
import { AboutDialogComponent } from '../about-dialog/about-dialog.component';
import { HowtoDialogComponent } from '../howto-dialog/howto-dialog.component';

@Component({
    templateUrl: './city-details-dialog.component.html',
    styleUrls: ['./city-details-dialog.component.css']
})
export class CityDetailsDialogComponent extends Unsubscriber implements OnInit {
    city: CityDTO;

    josmIsStarted: Observable<boolean>;
    osmID$: Observable<number>;

    cadastreLayer: any;

    updateButtonOpts: MatProgressButtonOptions = {
        active: false,
        text: 'Rafraîchir',
        buttonColor: 'primary',
        barColor: 'primary',
        raised: true,
        stroked: false,
        mode: 'indeterminate',
        value: 0,
        disabled: false
    };
    moreRecentDate: string;
    lastImport: string;

    constructor(
        @Inject(MAT_DIALOG_DATA) private readonly data: [CityDTO, any],
        public josmService: JosmService,
        public batimapService: BatimapService,
        private readonly dialogRef: MatDialogRef<CityDetailsDialogComponent>,
        private readonly legendService: LegendService,
        private readonly matDialog: MatDialog
    ) {
        super();
        this.city = data[0];
        this.cadastreLayer = data[1];
        this.lastImport = this.computeLastImport();
        if (this.city)
            this.osmID$ = this.batimapService.cityOsmID(this.city.insee);
    }

    ngOnInit(): void {
        if (localStorage.getItem('first-time-howto') !== 'false') {
            this.matDialog.open(HowtoDialogComponent);
        }

        this.josmIsStarted = this.josmService.isStarted();
    }

    // no need to add hostListener here, there is already one present for help
    openHelp() {
        this.matDialog.open(AboutDialogComponent);
    }

    @HostListener('document:keydown.f') close() {
        this.dialogRef.close(0);
    }

    @HostListener('document:keydown.r') updateCity() {
        this.updateButtonOpts.active = true;
        this.autoUnsubscribe(
            this.batimapService.updateCity(this.city.insee).subscribe(
                task => {
                    this.updateButtonOpts.text = `Rafraîchir (${task.progress.current}%)`;
                    if (task.state === TaskState.SUCCESS) {
                        this.city = task.result;
                        this.cadastreLayer.redraw();
                    }
                },
                undefined,
                () => {
                    this.updateButtonOpts.active = false;
                    this.updateButtonOpts.text = 'Rafraîchir';
                }
            )
        );
    }

    computeLastImport(): string {
        const d = this.city ? this.city.date : undefined;
        if (!d || d === 'never') {
            return "Le bâti n'a jamais été importé.";
        }
        if (d === 'raster') {
            return "Ville raster, pas d'import possible.";
        }
        if (d === 'unfinished') {
            return 'Des bâtiments sont de géométrie simple, à vérifier.';
        }
        if (Number.isInteger(+d)) {
            return `Dernier import en ${d}.`;
        }

        return 'Le bâti existant ne semble pas provenir du cadastre.';
    }

    cityDateChanged(newDate: string) {
        this.moreRecentDate = newDate;
        this.city.date = newDate;
        this.lastImport = this.computeLastImport();
    }

    editNode(node: number) {
        this.josmService.openNode(node, this.city).subscribe();
    }
}
