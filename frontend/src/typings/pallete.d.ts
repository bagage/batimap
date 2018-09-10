import * as palette from 'google-palette';

declare module 'google-palette' {
  namespace palette {
    export function palette(scheme: string, number: number, opt_index?: number, varargs?: any): string[];
  }
}
