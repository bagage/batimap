import { Injectable } from '@angular/core';
import * as palette from 'google-palette';
import { LegendDTO } from '../classes/legend.dto';

@Injectable({
    providedIn: 'root'
})
export class LegendService {
    city2date: Map<string, string> = new Map<string, string>();

    isActive(legend: LegendDTO | string): boolean {
        if (!legend) {
            console.warn('legend is null!!!');

            return true;
        }
        const id = typeof legend === 'string' ? legend : legend.name;

        return this.getLocalStorage(id) !== 'false';
    }

    setActive(legend: LegendDTO, isActive: boolean) {
        if (legend) {
            if (isActive) {
                localStorage.removeItem(legend.name);
            } else {
                localStorage.setItem(legend.name, 'false');
            }
        }
    }

    getLocalStorage(key: string): string | null {
        return localStorage.getItem(key);
    }

    date2color(yearStr: string): string {
        const currentYear = new Date().getFullYear();
        const oldestYear = 2008;
        if (Number.isInteger(+yearStr)) {
            const year = Number.parseInt(yearStr, 10);
            if (year === currentYear) {
                return 'green';
            }
            if (year >= oldestYear) {
                // last generated color is black and we do not want to use it
                // because it already represents raster cities
                const colorsCount = currentYear - oldestYear + 1;
                const colors: string[] = palette('tol-sq', colorsCount).map(
                    it => `#${it}`
                );

                return colors[currentYear - year];
            }
        }
        if (yearStr === 'raster') {
            return 'black';
        }
        if (yearStr === 'never') {
            return 'pink';
        }
        if (yearStr === 'unfinished') {
            return 'orange';
        }

        // unknown
        return 'gray';
    }

    date2name(yearStr: string) {
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
