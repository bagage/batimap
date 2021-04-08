import * as L from 'leaflet';

declare module 'leaflet-vectorgrid' {
    namespace vectorGrid {
        export function protobuf(url: string, options?: any): any;
    }
}
