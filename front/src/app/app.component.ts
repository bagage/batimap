import { Component, TemplateRef } from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import { MatIconRegistry } from '@angular/material/icon';
import { DomSanitizer, Title } from '@angular/platform-browser';
import { environment } from '../environments/environment';
import { LocalStorage } from './classes/local-storage';
import { AboutDialogComponent } from './components/about-dialog/about-dialog.component';
import { JosmScriptUpdateDialogComponent } from './components/josm-script-update-dialog/josm-script-update-dialog.component';

@Component({
    selector: 'app-root',
    templateUrl: './app.component.html',
    styleUrls: ['./app.component.css'],
})
export class AppComponent {
    constructor(
        private readonly matDialog: MatDialog,
        titleService: Title,
        matIconRegistry: MatIconRegistry,
        domSanitizer: DomSanitizer
    ) {
        const version = environment.version;
        titleService.setTitle(`État du bâti dans OSM (${version})`);

        if (LocalStorage.asBool('first-time-help', true)) {
            this.openDialog(AboutDialogComponent);
        } else if (JosmScriptUpdateDialogComponent.shouldDisplayDialog()) {
            this.openDialog(JosmScriptUpdateDialogComponent);
        }

        ['josm', 'osm'].forEach(icon => {
            matIconRegistry.addSvgIcon(icon, domSanitizer.bypassSecurityTrustResourceUrl(`../assets/${icon}.svg`));
        });
    }

    private openDialog(dialog: any): void {
        // open asyncly because otherwise on chrome the popup is immediately closed
        setTimeout(() => this.matDialog.open(dialog), 1000);
    }
}
