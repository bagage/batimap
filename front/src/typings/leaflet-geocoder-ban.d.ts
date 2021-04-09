declare namespace L {
    interface GeocoderBanOptions {
        position?: string; // 'topleft',
        style?: string; // 'control',
        placeholder?: string; // 'adresse',
        resultsNumber?: number; // 7,
        collapsed?: boolean; // true,
        serviceUrl?: string; // 'https?: string; ////api-adresse.data.gouv.fr/search/',
        minIntervalBetweenRequests?: number; // 250,
        defaultMarkgeocode?: boolean; // true,
        autofocus?: boolean; // true
    }
    export function geocoderBAN(options: GeocoderBanOptions): L.Control;
}
