import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
    name: 'any',
})
export class AnyPipe implements PipeTransform {
    transform(input: any): any {
        return input;
    }
}
