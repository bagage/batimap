import {Injectable} from '@angular/core';
import {LegendDTO} from '../classes/legend.dto';
// import {palette} from 'palette';

@Injectable({
  providedIn: 'root'
})
export class LegendService {
  public isActive(legend: LegendDTO | string): boolean {
    return 'true' === this.getLocalStorage(typeof legend === 'string' ? legend : legend.name);
  }

  public setActive(legend: LegendDTO, isActive: boolean) {
    return localStorage.setItem(legend.name, isActive ? 'true' : null);
  }

  public getLocalStorage(key: string) {
    return localStorage.getItem(key);
  }

  public date2color(yearStr: string): string {
    const currentYear = new Date().getFullYear();
    const oldestYear = 2009;
    if (Number.isInteger(+yearStr)) {
      const year = Number.parseInt(yearStr, 10);
      if (year === currentYear) {
        return 'green';
      } else if (year >= oldestYear) {
        /*last color is black and we do not want to use it for this because it represents raster cities*/
        const colorsCount = currentYear - oldestYear + 1;
        // const colors: string[] = palette('tol-sq', colorsCount).map(it => '#' + it);
        // return colors[currentYear - year];
        return 'red'
      }
    } else if (yearStr === 'raster') {
      return 'black';
    } else if (yearStr === 'never') {
      return 'pink';
    }
    // unknown
    return 'gray';
  }
}
