import { LegendDTO } from '../../classes/legend.dto';

export class MapDateLegendModel extends LegendDTO {
    constructor(
        public name: string, // legend ID
        public checked: boolean, // is the legend item checked or not
        public count: number, // number of items of this item on the map
        public percent: number, // number of items of this item relative to the total number on the map
        public displayName: string, // legend display name
        public color: string
    ) {
        super();
    }
}
