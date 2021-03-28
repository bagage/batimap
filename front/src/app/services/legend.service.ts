import { Injectable } from '@angular/core';
import { palette } from '../classes/colors';
import { LegendDTO } from '../classes/legend.dto';

@Injectable({
    providedIn: 'root',
})
export class LegendService {
    city2date: Map<string, string> = new Map<string, string>();
    inactiveLegendItems = new Set<string>();
    storageName = 'deactivated-legends';

    oldestYear = 2008;
    currentYear = new Date().getFullYear();
    yearColors = palette(this.currentYear - this.oldestYear + 1);

    constructor() {
        const ignored = localStorage.getItem(this.storageName);
        if (ignored) {
            ignored.split(',').map(v => this.inactiveLegendItems.add(v));
        }
    }

    isActive(legend: LegendDTO | string): boolean {
        const id = typeof legend === 'string' ? legend : legend.name;

        return !this.inactiveLegendItems.has(id);
    }

    toggleActive(legend: LegendDTO, isActive: boolean) {
        if (legend) {
            const currentActive = !this.inactiveLegendItems.has(legend.name);
            if (currentActive !== isActive) {
                if (isActive) {
                    this.inactiveLegendItems.delete(legend.name);
                } else {
                    this.inactiveLegendItems.add(legend.name);
                }
                // persist settings
                const value = [];
                this.inactiveLegendItems.forEach(v => value.push(v));
                if (value.length > 0) {
                    localStorage.setItem(this.storageName, value.join(','));
                } else {
                    localStorage.removeItem(this.storageName);
                }
            }
        }
    }

    date2color(yearStr: string): string {
        if (Number.isInteger(+yearStr)) {
            const year = Number.parseInt(yearStr, 10);
            if (year >= this.oldestYear) {
                return this.yearColors[this.currentYear - year];
            }
        }
        if (yearStr === 'raster') {
            return 'black';
        }
        if (yearStr === 'never') {
            return 'pink';
        }
        if (yearStr === 'unfinished') {
            return '#03A9F4';
        }
        if (yearStr === 'ignored') {
            return '#666';
        }

        // unknown
        return '#6200EE';
    }

    date2name(yearStr: string) {
        if (yearStr === 'ignored') {
            return 'ignoré';
        }
        if (!yearStr || yearStr === 'never') {
            return 'jamais import';
        }
        if (yearStr === 'raster') {
            return 'non dispo.';
        }
        if (yearStr === 'unfinished') {
            return 'simplifié';
        }
        if (Number.isInteger(+yearStr)) {
            return yearStr;
        }

        return 'indéterminé';
    }
}
