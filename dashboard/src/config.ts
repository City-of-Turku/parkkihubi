import { Point } from './components/types';

export const isDev: boolean = (import.meta.env.MODE === 'development');

export const apiBaseUrl: string = import.meta.env.VITE_API_URL || (
    (isDev)
        ? 'http://localhost:8000/'
        : window.location.href.includes('test')
            ? 'https://testiparkki.turku.fi/'
            : 'https://parkki.turku.fi/');

export const mapTilesUrl: string = import.meta.env.VITE_MAPTILES_URL || (
    (isDev || window.location.href.includes('test'))
        ? 'https://maptiles-testi.turku.fi/styles/hel-osm-bright/{z}/{x}/{y}{r}.png'
        : 'https://maptiles.turku.fi/styles/hel-osm-bright/{z}/{x}/{y}{r}.png');

let mapPoint: Point;
if (typeof import.meta.env.VITE_API_CENTER !== 'undefined') {
    const envPoint = import.meta.env.VITE_API_CENTER!.split(',').map(Number);
    mapPoint = [envPoint[0], envPoint[1]];
} else {
    mapPoint = [60.45148, 22.26869]; // Default to Turku centrum
}
export const centerCoordinates: Point = mapPoint;
