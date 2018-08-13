import * as L from "leaflet";

declare module "leaflet" {
  namespace vectorGrid {
    export function protobuf(url: string, options?: any): any;
  }
}
