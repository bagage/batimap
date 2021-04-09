import { Component, HostListener, OnDestroy } from '@angular/core';
import { MatDialog, MatDialogRef } from '@angular/material/dialog';
import { environment } from '../../../environments/environment';
import { HowtoDialogComponent } from '../howto-dialog/howto-dialog.component';
import { JosmScriptUpdateDialogComponent } from '../josm-script-update-dialog/josm-script-update-dialog.component';

@Component({
    selector: 'app-about-dialog',
    templateUrl: './about-dialog.component.html',
    styleUrls: ['./about-dialog.component.css'],
})
export class AboutDialogComponent implements OnDestroy {
    version = environment.version;

    constructor(
        private readonly matDialog: MatDialog,
        private readonly dialogRef: MatDialogRef<AboutDialogComponent>
    ) {}

    ngOnDestroy(): void {
        localStorage.setItem('first-time-help', 'false');
        localStorage.setItem(JosmScriptUpdateDialogComponent.storageKey, environment.version);
    }

    @HostListener('document:keydown.m') showHowto(): void {
        this.matDialog.open(HowtoDialogComponent);
    }

    @HostListener('document:keydown.g') close(): void {
        this.dialogRef.close(0);
    }
}
