import { MatProgressButtonOptions } from "mat-progress-buttons";
import { Observable } from "rxjs";
import { CityDTO } from "../../classes/city.dto";
import { Component, HostListener, Inject, OnInit } from "@angular/core";
import { MAT_DIALOG_DATA, MatDialog, MatDialogRef } from "@angular/material";
import { JosmService } from "../../services/josm.service";
import { BatimapService } from "../../services/batimap.service";
import { LegendService } from "../../services/legend.service";
import { HowtoDialogComponent } from "../howto-dialog/howto-dialog.component";
import { filter } from "rxjs/operators";
import { Unsubscriber } from "../../classes/unsubscriber";
import { AboutDialogComponent } from "../about-dialog/about-dialog.component";

@Component({
  templateUrl: "./city-details-dialog.component.html",
  styleUrls: ["./city-details-dialog.component.css"]
})
export class CityDetailsDialogComponent extends Unsubscriber implements OnInit {
  city: CityDTO;
  josmIsStarted: Observable<boolean>;

  cadastreLayer: any;

  updateButtonOpts: MatProgressButtonOptions = {
    active: false,
    text: "Rafraîchir",
    buttonColor: "primary",
    barColor: "primary",
    raised: true,
    stroked: false,
    mode: "indeterminate",
    value: 0,
    disabled: false
  };
  moreRecentDate: string;

  constructor(
    @Inject(MAT_DIALOG_DATA) private data: [CityDTO, any],
    public josmService: JosmService,
    public batimapService: BatimapService,
    private dialogRef: MatDialogRef<CityDetailsDialogComponent>,
    private legendService: LegendService,
    private matDialog: MatDialog
  ) {
    super();
    this.city = data[0];
    this.cadastreLayer = data[1];
  }

  ngOnInit(): void {
    if (localStorage.getItem("first-time-howto") !== "false") {
      this.matDialog.open(HowtoDialogComponent);
    }

    this.josmIsStarted = this.josmService.isStarted();
  }

  // no need to add hostListener here, there is already one present for help
  openHelp() {
    this.matDialog.open(AboutDialogComponent);
  }

  @HostListener("document:keydown.f")
  close() {
    this.dialogRef.close(0);
  }

  @HostListener("document:keydown.r")
  updateCity() {
    this.updateButtonOpts.active = true;
    this.autoUnsubscribe(
      this.batimapService
        .updateCity(this.city.insee)
        .pipe(filter(x => x.result !== null))
        .subscribe(
          progress => {
            this.updateButtonOpts.active = false;
            this.city = progress.result;
            this.cadastreLayer.redraw();
          },
          () => (this.updateButtonOpts.active = false)
        )
    );
  }

  lastImport(d): string {
    if (!d || d === "never") {
      return 'Le bâti n\'a jamais été importé.';
    } else if (d === "raster") {
      return 'Ville raster, pas d\'import possible.';
    } else if (Number.isInteger(+d)) {
      return `Dernier import en ${d}.`;
    } else {
      return "Le bâti existant ne semble pas provenir du cadastre.";
    }
  }

  get detailsEntry(): [string, string][] {
    if (this.city && this.city.details) {
      let json;
      try {
        json = JSON.parse(this.city.details);
      } catch {
        json = this.city.details;
      }
      if (json && json.dates) {
        return Object.entries(json.dates);
      }
    }
    return [];
  }

  cityDateChanged(newDate: string) {
    this.moreRecentDate = newDate;
    this.city.date = newDate;
  }
}
