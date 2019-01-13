import { Injectable } from "@angular/core";
import { LegendDTO } from "../classes/legend.dto";
import * as palette from "google-palette";

@Injectable({
  providedIn: "root"
})
export class LegendService {
  public city2date: Map<string, string> = new Map<string, string>();

  public isActive(legend: LegendDTO | string): boolean {
    if (!legend) {
      console.warn("legend is null!!!");
      return true;
    }
    return (
      "false" !==
      this.getLocalStorage(typeof legend === "string" ? legend : legend.name)
    );
  }

  public setActive(legend: LegendDTO, isActive: boolean) {
    if (legend) {
      localStorage.setItem(legend.name, isActive ? null : "false");
    }
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
        return "green";
      } else if (year >= oldestYear) {
        /*last color is black and we do not want to use it for this because it represents raster cities*/
        const colorsCount = currentYear - oldestYear + 1;
        const colors: string[] = palette("tol-sq", colorsCount).map(
          it => "#" + it
        );
        return colors[currentYear - year];
      }
    } else if (yearStr === "raster") {
      return "black";
    } else if (yearStr === "never") {
      return "pink";
    } else if (yearStr === "unfinished") {
      return "orange";
    }
    // unknown
    return "gray";
  }

  date2name(yearStr: string) {
    if (!yearStr || yearStr === "never") {
      return "jamais import";
    } else if (yearStr === "raster") {
      return "non dispo.";
    } else if (yearStr === "unfinished") {
      return "simplifié";
    } else if (Number.isInteger(+yearStr)) {
      return yearStr;
    } else {
      return "indéterminé";
    }
  }
}
