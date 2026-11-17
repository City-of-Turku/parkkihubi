import * as geojson from 'geojson';

export type Point = [number, number];

export interface MapViewport {
    center: Point;
    zoom: number;
    bounds?: {
        neLat: number;
        neLng: number;
        swLat: number;
        swLng: number;
    };
}

export interface Region extends
geojson.Feature<geojson.MultiPolygon, RegionProperties> {
    id: string;
}

export interface PermitArea extends
geojson.Feature<geojson.MultiPolygon, PermitAreaProperties> {
    id: number;
}

export interface PermitAreaProperties {
    identifier: string;
    name: string;
    areaKm2: number;
    permitCount?: number;
}

export interface RegionProperties {
    name: string;
    capacityEstimate: number;
    areaKm2: number;
    spotsPerKm2: number;
    parkingAreas?: string[];
    parkingCount?: number;
    isSelected?: boolean;
}
