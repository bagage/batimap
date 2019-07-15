import { Component, OnDestroy } from '@angular/core';
import { environment } from '../../../environments/environment';
import { JosmScriptUpdateDialogComponent } from '../josm-script-update-dialog/josm-script-update-dialog.component';

@Component({
    selector: 'app-howto-dialog',
    templateUrl: './howto-dialog.component.html',
    styleUrls: ['./howto-dialog.component.css']
})
export class HowtoDialogComponent implements OnDestroy {
    ngOnDestroy() {
        localStorage.setItem('first-time-howto', 'false');
        localStorage.setItem(
            JosmScriptUpdateDialogComponent.storageKey,
            environment.version
        );
    }
}
