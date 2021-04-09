export class LocalStorage {
    static get(key: string, defaultValue: string): string {
        const value = localStorage.getItem(key);
        if (value === null) {
            return defaultValue;
        }

        return value;
    }

    static number(key: string, defaultValue: number): number {
        return +LocalStorage.get(key, defaultValue.toString());
    }
    static bool(key: string, defaultValue: boolean): boolean {
        return LocalStorage.get(key, defaultValue ? 'true' : 'false') === 'true';
    }
}
