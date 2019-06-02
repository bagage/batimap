import { Component } from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import { Title } from '@angular/platform-browser';
import { environment } from '../environments/environment';
import { AboutDialogComponent } from './components/about-dialog/about-dialog.component';
import { JosmScriptUpdateDialogComponent } from './components/josm-script-update-dialog/josm-script-update-dialog.component';

@Component({
    selector: 'app-root',
    templateUrl: './app.component.html',
    styleUrls: ['./app.component.css']
})
export class AppComponent {
    constructor(private matDialog: MatDialog, titleService: Title) {
        const version = environment.version;
        titleService.setTitle(`État du bâti dans OSM (${version})`);

        if (localStorage.getItem('first-time-help') !== 'false') {
            this.openDialog(AboutDialogComponent);
        } else if (JosmScriptUpdateDialogComponent.shouldDisplayDialog()) {
            this.openDialog(JosmScriptUpdateDialogComponent);
        }
    }

    private openDialog(dialog) {
        // open asyncly because otherwise on chrome the popup is immediately closed
        setTimeout(() => this.matDialog.open(dialog), 1000);
    }
}
