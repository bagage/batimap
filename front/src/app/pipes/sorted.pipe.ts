import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
    name: 'sorted',
})
export class SortedPipe implements PipeTransform {
    transform(objects: any[]): any {
        return objects.sort();
    }
}
