import {Component, OnDestroy} from '@angular/core';
import {environment} from '../../../environments/environment';

@Component({
  selector: 'app-about-dialog',
  templateUrl: './about-dialog.component.html',
  styleUrls: ['./about-dialog.component.css']
})
export class AboutDialogComponent implements OnDestroy {
  version = environment.version;

  ngOnDestroy() {
    localStorage.setItem('first-time-help', 'false');
  }
}
