import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
    name: 'map'
})
export class MapPipe implements PipeTransform {
    transform(objects: any[], attribute: string): any {
        return objects.map(it => it[attribute]);
    }
}
