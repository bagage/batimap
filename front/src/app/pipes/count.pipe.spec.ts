import { CountPipe } from './count.pipe';

describe('CountPipe', () => {
    it('create an instance', () => {
        const pipe = new CountPipe();
        expect(pipe).toBeTruthy();
    });
    it('return array length', () => {
        const pipe = new CountPipe();
        expect(pipe.transform([])).toEqual(0);
        expect(pipe.transform([1, 2, 3])).toEqual(3);
    });
    it('return map size', () => {
        const pipe = new CountPipe();
        expect(pipe.transform(new Map<string, string>())).toEqual(0);
        const map = new Map<string, string>();
        map.set('a', 'a');
        map.set('b', 'b');
        expect(pipe.transform(map)).toEqual(2);
    });
    it('return object properties count', () => {
        const pipe = new CountPipe();
        expect(pipe.transform(undefined)).toEqual(0);
        expect(pipe.transform({})).toEqual(0);
        expect(
            pipe.transform({
                first: 1,
                second: 'anotherString',
                property: 'prop'
            })
        ).toEqual(3);
    });
});
