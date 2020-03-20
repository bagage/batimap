import { async } from '@angular/core/testing';
import { deserialize, plainToClass } from 'class-transformer';
import { CityDTO, StatsDetailsDTO } from './city.dto';

describe('CityDTO', () => {
    it('should convert CityDetails plain to class', async(() => {
        const given = '{"simplified": [1, 2], "dates": {"unknown": 1087, "2012": 2}}';
        const result = deserialize(StatsDetailsDTO, given);
        expect(result.simplified).toEqual([1, 2]);
        expect(result.dates).toEqual(new Map().set('unknown', 1087).set('2012', 2));
    }));
    it('should convert City plain to class', async(() => {
        const given = '{"name": "city", "details": {"simplified": [1, 2], "dates": {"unknown": 1087, "2012": 2}}}';
        const expected = new CityDTO();
        expected.name = 'city';
        expected.details = new StatsDetailsDTO();
        expected.details.simplified = [1, 2];
        expected.details.dates = new Map().set('unknown', 1087).set('2012', 2);

        const result = deserialize(CityDTO, given);
        expect(result).toEqual(expected);
    }));
});
