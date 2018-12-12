import { Component } from "@angular/core";
import { MatDialog } from "@angular/material";
import { AboutDialogComponent } from "./components/about-dialog/about-dialog.component";
import { Title } from "@angular/platform-browser";
import { environment } from "../environments/environment";

@Component({
  selector: "app-root",
  templateUrl: "./app.component.html",
  styleUrls: ["./app.component.css"]
})
export class AppComponent {
  constructor(matDialog: MatDialog, titleService: Title) {
    const version = environment.version;
    titleService.setTitle(`État du bâti dans OSM (${version})`);

    if (localStorage.getItem("first-time-help") !== "false") {
      matDialog.open(AboutDialogComponent);
    }
  }
}
