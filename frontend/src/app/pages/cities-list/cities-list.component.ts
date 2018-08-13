import {Component, OnInit, ViewChild} from '@angular/core';
import {MatSort, MatTableDataSource} from '@angular/material';

export interface City {
  name: string;
  insee: string;
  author: string;
  date: string;
  contributionDetails: any;
}


const ELEMENT_DATA: City[] = [
  {name: 'Clerieux', insee: '20', author: 'moi', date: '2018', contributionDetails: null},
  {name: 'Cleraieux', insee: '21', author: 'maoi', date: '2017', contributionDetails: null},
]

@Component({
  selector: 'app-cities-list',
  templateUrl: './cities-list.component.html',
  styleUrls: ['./cities-list.component.css']
})
export class CitiesListComponent implements OnInit {

  displayedColumns: string[] = ['name', 'insee', 'author', 'date', 'details'];
  dataSource = new MatTableDataSource(ELEMENT_DATA);

  @ViewChild(MatSort) sort: MatSort;

  ngOnInit() {
    this.dataSource.sort = this.sort;
  }
}
