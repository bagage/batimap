import {Component, Input, OnInit, ViewChild} from '@angular/core';
import {MatSort, MatTableDataSource} from '@angular/material';
import {BatimapService} from '../../services/batimap.service';
import {CityDTO} from '../../classes/city.dto';
import {JosmService} from '../../services/josm.service';
import {Observable} from 'rxjs';
import * as L from 'leaflet';

@Component({
  selector: 'app-cities-list',
  templateUrl: './cities-list.component.html',
  styleUrls: ['./cities-list.component.css']
})
export class CitiesListComponent implements OnInit {
  @Input() map: L.Map;

  displayedColumns: string[] = ['name', 'insee', 'date', 'details', 'actions'];
  dataSource = new MatTableDataSource<CityDTO>();
  isReady: boolean;
  josmReady$: Observable<boolean>;

  @ViewChild(MatSort) sort: MatSort;

  constructor(private batimapService: BatimapService, public josmService: JosmService) {
  }

  ngOnInit() {
    this.dataSource.sort = this.sort;
    this.josmReady$ = this.josmService.isStarted();

    this.refreshDataSource();
    this.map.on('moveend', () => {
      this.refreshDataSource();
    });
  }

  private refreshDataSource() {
    this.isReady = false;
    this.batimapService.citiesInBbox(this.map.getBounds()).subscribe((cities: CityDTO[]) => {
      this.dataSource.data = null;
      this.dataSource.data = cities;
      this.isReady = true;
    });
  }
}
