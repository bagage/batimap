export class MockAppConfigService {
    getConfig() {
        return {
            backendServerUrl: 'http://localhost:5000/',
            tilesServerUrl:
                'http://localhost:9999/maps/batimap/{z}/{x}/{y}.vector.pbf'
        };
    }
}
