import {BrowserModule} from '@angular/platform-browser';
import {NgModule} from '@angular/core';

import {AppComponent} from './app.component';
import {LeafletModule} from '@asymmetrik/ngx-leaflet';
import {RouterModule, Routes} from '@angular/router';
import {MapComponent} from './pages/map/map.component';
import {PagesModule} from './pages/pages.module';
import {BrowserAnimationsModule} from '@angular/platform-browser/animations';
import {JosmService} from './services/josm.service';
import {HttpClientModule} from '@angular/common/http';
import { JosmButtonComponent } from './components/josm-button/josm-button.component';


const appRoutes: Routes = [
  {path: '', component: MapComponent}
];

@NgModule({
  declarations: [
    AppComponent
  ],
  imports: [
    BrowserAnimationsModule,
    BrowserModule,
    HttpClientModule,
    PagesModule,
    LeafletModule.forRoot(),
    RouterModule.forRoot(
      appRoutes
      // ,{enableTracing: true}
    )
  ],
  providers: [JosmService],
  bootstrap: [AppComponent]
})
export class AppModule {
}
