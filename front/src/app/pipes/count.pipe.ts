import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
    name: 'count',
    pure: true,
})
export class CountPipe implements PipeTransform {
    transform(value: any, ...args: any[]): any {
        if (!value) {
            return 0;
        }
        if (value.length !== undefined) {
            return value.length;
        }
        if (value.size !== undefined) {
            return value.size;
        }

        return Object.keys(value).length;
    }
}
