import { Component, HostListener, OnDestroy } from '@angular/core';
import { MatDialog, MatDialogRef } from '@angular/material/dialog';
import { environment } from '../../../environments/environment';
import { HowtoDialogComponent } from '../howto-dialog/howto-dialog.component';

@Component({
    selector: 'app-about-dialog',
    templateUrl: './about-dialog.component.html',
    styleUrls: ['./about-dialog.component.css']
})
export class AboutDialogComponent implements OnDestroy {
    version = environment.version;

    constructor(
        private readonly matDialog: MatDialog,
        private readonly dialogRef: MatDialogRef<AboutDialogComponent>
    ) {}

    ngOnDestroy() {
        localStorage.setItem('first-time-help', 'false');
    }

    @HostListener('document:keydown.m') showHowto() {
        this.matDialog.open(HowtoDialogComponent);
    }

    @HostListener('document:keydown.g') close() {
        this.dialogRef.close(0);
    }
}
