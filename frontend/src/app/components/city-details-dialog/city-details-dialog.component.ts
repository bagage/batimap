import { MatProgressButtonOptions } from "mat-progress-buttons";
import { Observable } from "rxjs";
import { CityDTO } from "../../classes/city.dto";
import { Component, HostListener, Inject, OnInit } from "@angular/core";
import { MAT_DIALOG_DATA, MatDialog, MatDialogRef } from "@angular/material";
import { JosmService } from "../../services/josm.service";
import { BatimapService } from "../../services/batimap.service";
import { LegendService } from "../../services/legend.service";
import { HowtoDialogComponent } from "../howto-dialog/howto-dialog.component";

@Component({
  templateUrl: "./city-details-dialog.component.html",
  styleUrls: ["./city-details-dialog.component.css"]
})
export class CityDetailsDialogComponent implements OnInit {
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

  constructor(
    @Inject(MAT_DIALOG_DATA) private data: [CityDTO, any],
    public josmService: JosmService,
    public batimapService: BatimapService,
    private dialogRef: MatDialogRef<CityDetailsDialogComponent>,
    private legendService: LegendService,
    private matDialog: MatDialog
  ) {
    this.city = data[0];
    this.cadastreLayer = data[1];
  }

  ngOnInit(): void {
    if (localStorage.getItem("first-time-howto") !== "false") {
      this.matDialog.open(HowtoDialogComponent);
    }

    this.josmIsStarted = this.josmService.isStarted();
  }

  @HostListener("document:keydown.f")
  close() {
    this.dialogRef.close(0);
  }

  @HostListener("document:keydown.r")
  updateCity() {
    this.updateButtonOpts.active = true;
    this.batimapService.updateCity(this.city.insee).subscribe(
      result => {
        this.updateButtonOpts.active = false;
        this.city = result;
        this.cadastreLayer.redraw();
      },
      () => (this.updateButtonOpts.active = false)
    );
  }

  lastImport(): string {
    const d = this.city.date;
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
}
