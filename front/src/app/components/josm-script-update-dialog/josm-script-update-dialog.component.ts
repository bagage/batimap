import { Component, OnDestroy } from '@angular/core';
import { environment } from '../../../environments/environment';

@Component({
    selector: 'app-josm-script-update-dialog',
    templateUrl: './josm-script-update-dialog.component.html',
    styleUrls: ['./josm-script-update-dialog.component.css']
})
export class JosmScriptUpdateDialogComponent implements OnDestroy {
    static storageKey = 'josm-scripts-version';

    static strictlyLowerThanVersion(version1: string, version2: string): boolean {
        const part1 = version1.match('(\\d+).(\\d+).(\\d+)');
        const part2 = version2.match('(\\d+).(\\d+).(\\d+)');

        for (let i = 1; i < part1.length; i += 1) {
            const diff = Number.parseInt(part1[i], 10) - Number.parseInt(part2[i], 10);
            if (diff !== 0) {
                return diff < 0;
            }
        }

        return false;
    }

    static shouldDisplayDialog(): boolean {
        const userVersion = localStorage.getItem(JosmScriptUpdateDialogComponent.storageKey) || '0.0.0';

        return JosmScriptUpdateDialogComponent.strictlyLowerThanVersion(userVersion, environment.version);
    }

    ngOnDestroy() {
        localStorage.setItem(JosmScriptUpdateDialogComponent.storageKey, environment.version);
    }
}
