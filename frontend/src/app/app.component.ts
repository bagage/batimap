import {AfterViewInit, Component, OnInit} from '@angular/core';
import {MatDialog} from '@angular/material';
import {AboutDialogComponent} from './pages/about-dialog/about-dialog.component';
import {Title} from '@angular/platform-browser';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent {
  constructor(matDialog: MatDialog, titleService: Title) {
    titleService.setTitle('État du bâti dans OSM');

    if (localStorage.getItem('first-time-help') !== 'false') {
      matDialog.open(AboutDialogComponent);
    }
  }
}
