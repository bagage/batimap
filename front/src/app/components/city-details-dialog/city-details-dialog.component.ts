import { Component, HostListener, Inject, OnInit } from '@angular/core';
import { MatDialog, MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { MatProgressButtonOptions } from 'mat-progress-buttons';
import { Observable } from 'rxjs';
import { CityDTO } from '../../classes/city.dto';
import { Unsubscriber } from '../../classes/unsubscriber';
import { BatimapService, TaskState } from '../../services/batimap.service';
import { JosmService } from '../../services/josm.service';
import { AboutDialogComponent } from '../about-dialog/about-dialog.component';
import { HowtoDialogComponent } from '../howto-dialog/howto-dialog.component';

@Component({
    templateUrl: './city-details-dialog.component.html',
    styleUrls: ['./city-details-dialog.component.css'],
})
export class CityDetailsDialogComponent extends Unsubscriber implements OnInit {
    city: CityDTO;

    josmIsStarted: Observable<boolean>;
    osmID: number;

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
        disabled: false,
    };
    moreRecentDate: boolean;
    lastImport: string;

    constructor(
        @Inject(MAT_DIALOG_DATA) data: [CityDTO, number, any],
        public josmService: JosmService,
        public batimapService: BatimapService,
        private readonly dialogRef: MatDialogRef<CityDetailsDialogComponent>,
        private readonly matDialog: MatDialog
    ) {
        super();
        this.city = data[0];
        this.osmID = data[1];
        this.cadastreLayer = data[2];
        this.computeLastImport();
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

    isCityIgnored() {
        return this.batimapService.ignoredInsees().indexOf(this.city.insee) !== -1;
    }

    @HostListener('document:keydown.i') toggleIgnoreCity() {
        // tslint:disable
        var ignoredCities = this.batimapService.ignoredInsees();
        const cityIndex = ignoredCities.indexOf(this.city.insee);
        if (cityIndex !== -1) {
            ignoredCities.splice(cityIndex);
        } else {
            ignoredCities.push(this.city.insee);
        }
        this.batimapService.updateIgnoredInsees(ignoredCities);
        this.dialogRef.close(0);
        this.cadastreLayer.redraw();
    }

    @HostListener('document:keydown.r') updateCity() {
        const onEnd = () => {
            this.updateButtonOpts.active = false;
            this.updateButtonOpts.text = 'Rafraîchir';
        };

        this.updateButtonOpts.active = true;
        this.autoUnsubscribe(
            this.batimapService.updateCity(this.city.insee).subscribe(
                task => {
                    this.updateButtonOpts.text = `Rafraîchir (${task.progress.current}%)`;
                    if (task.state === TaskState.SUCCESS) {
                        this.cityDateChanged(task.result);
                        this.cadastreLayer.redraw();
                    }
                },
                onEnd,
                onEnd
            )
        );
    }

    computeLastImport() {
        const d = this.city ? this.city.date : undefined;
        let val: string;
        if (!d || d === 'never') {
            val = "Le bâti n'a jamais été importé.";
        } else if (d === 'raster') {
            val = "Ville raster, pas d'import possible.";
        } else if (d === 'unfinished') {
            val = 'Des bâtiments sont de géométrie simple, à vérifier.';
        } else if (Number.isInteger(+d)) {
            val = `Dernier import en ${d}.`;
        } else {
            val = 'Le bâti existant ne semble pas provenir du cadastre.';
        }
        this.lastImport = val;
    }

    cityDateChanged(city: CityDTO) {
        this.moreRecentDate = this.city.date !== city.date;
        this.city = city;
        this.computeLastImport();
    }

    editNodes(nodes: number[]) {
        this.josmService.openNodes(nodes, this.city.insee, this.city.name).subscribe();
    }
}
