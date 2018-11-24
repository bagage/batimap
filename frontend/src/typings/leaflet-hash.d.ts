import * as L from 'leaflet';

declare module 'leaflet' {
  export function hash(map: L.Map): any;
}
