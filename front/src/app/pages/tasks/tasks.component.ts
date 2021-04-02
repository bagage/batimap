import { Component, OnInit } from '@angular/core';
import { combineLatest, Observable, of } from 'rxjs';
import { map, switchMap } from 'rxjs/operators';
import { TaskDTO } from '../../classes/task.dto';
import { BatimapService } from '../../services/batimap.service';

@Component({
    selector: 'app-tasks',
    templateUrl: './tasks.component.html',
    styleUrls: ['./tasks.component.css'],
})
export class TasksComponent implements OnInit {
    metatasks$: Observable<any>;

    constructor(private readonly batimapService: BatimapService) {}

    ngOnInit() {
        localStorage.setItem('displayTasks', 'true');
        this.metatasks$ = this.batimapService.tasks().pipe(
            switchMap((tasks: TaskDTO[]) => {
                const taskDetails$ = tasks.map(task =>
                    this.batimapService.waitTask<any>(task.task_id).pipe(map(status => ({ task, status })))
                );

                return taskDetails$.length ? combineLatest(taskDetails$) : of([]);
            })
        );
    }
}
