import { Component, HostListener, Inject } from '@angular/core';
import { MatDialog, MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { Observable } from 'rxjs';
import { StatsDetailsDTO } from '../../classes/city.dto';
import { DepartmentDTO } from '../../classes/department.dto';
import { BatimapService } from '../../services/batimap.service';
import { JosmService } from '../../services/josm.service';
import { AboutDialogComponent } from '../about-dialog/about-dialog.component';

@Component({
    templateUrl: './department-details-dialog.component.html',
    styleUrls: ['./department-details-dialog.component.css'],
})
export class DepartmentDetailsDialogComponent {
    department: DepartmentDTO;
    details$: Observable<StatsDetailsDTO>;
    osmId: number;
    lastImport: string;

    constructor(
        @Inject(MAT_DIALOG_DATA) data: [DepartmentDTO, number],
        public josmService: JosmService,
        private readonly dialogRef: MatDialogRef<DepartmentDetailsDialogComponent>,
        private readonly matDialog: MatDialog,
        batimapService: BatimapService
    ) {
        this.department = data[0];
        this.osmId = data[1];
        this.lastImport = this.computeLastImport();
        this.details$ = batimapService.departmentDetails(this.department.insee);
    }

    // no need to add hostListener here, there is already one present for help
    openHelp() {
        this.matDialog.open(AboutDialogComponent);
    }

    @HostListener('document:keydown.f') close() {
        this.dialogRef.close(0);
    }

    computeLastImport(): string {
        const d = this.department ? this.department.date : undefined;
        if (!d || d === 'never') {
            return "Le bâti n'a en majorité jamais été importé.";
        }
        if (d === 'raster') {
            return 'Département principalement raster.';
        }
        if (d === 'unfinished') {
            return 'Des bâtiments sont de géométrie simple, à vérifier.';
        }
        if (Number.isInteger(+d)) {
            return `Dernier import moyen sur l'ensemble du département en ${d}.`;
        }

        return 'Le bâti existant ne semble globalement pas provenir du cadastre.';
    }

    editNodes(nodes: [number]) {
        this.josmService.openNodes(nodes, this.department.insee, this.department.name).subscribe();
    }
}
