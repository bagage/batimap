import {Component, OnDestroy} from '@angular/core';
import {environment} from '../../../environments/environment';
import {MatDialog} from '@angular/material';
import {HowtoDialogComponent} from '../howto-dialog/howto-dialog.component';

@Component({
  selector: 'app-about-dialog',
  templateUrl: './about-dialog.component.html',
  styleUrls: ['./about-dialog.component.css']
})
export class AboutDialogComponent implements OnDestroy {
  version = environment.version;

  constructor(private matDialog: MatDialog) {
  }

  ngOnDestroy() {
    localStorage.setItem('first-time-help', 'false');
  }

  showHowto() {
    this.matDialog.open(HowtoDialogComponent);
  }
}
