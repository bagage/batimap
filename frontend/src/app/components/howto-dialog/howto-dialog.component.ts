import { Component, OnDestroy } from "@angular/core";

@Component({
  selector: "app-howto-dialog",
  templateUrl: "./howto-dialog.component.html",
  styleUrls: ["./howto-dialog.component.css"]
})
export class HowtoDialogComponent implements OnDestroy {
  ngOnDestroy() {
    localStorage.setItem("first-time-howto", "false");
  }
}
