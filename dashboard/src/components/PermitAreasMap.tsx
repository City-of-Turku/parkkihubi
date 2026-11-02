import * as geojson from 'geojson';
import * as Leaflet from 'leaflet';
import { GeoJSON, MapContainer } from 'react-leaflet';

import BaseMapLayers from './BaseMapLayers';
import { PermitArea, PermitAreaProperties, Point } from './types';

import './ParkingRegionsMap.css';

export interface Props {
    center: Point;
    zoom: number;
    areas?: PermitArea[];
}

export default function PermitAreasMap(props: Props) {
    const geoJsonElement = props.areas ? (
        <GeoJSON
            key={getKeyForAreas(props.areas)}
            data={getFeatureCollection(props.areas)}
            style={getStyleForArea}
            onEachFeature={bindPopupToArea}
        />
    ) : null;
    return (
        <MapContainer center={props.center} zoom={props.zoom}>
            <BaseMapLayers />
            {geoJsonElement}
        </MapContainer>
    );
}

const bindPopupToArea = (area: PermitArea, layer: Leaflet.Layer): void => {
    const props = area.properties;
    if (!props) {
        return;
    }
    layer.bindTooltip(`${props.identifier}: ${props.name}`);
    layer.bindPopup(`
        <h3>${props.name}</h3>
        <b>Tunnus</b>: ${props.identifier}<br>
        <b>Pinta-ala</b>: ${props.areaKm2.toFixed(2)} km<sup>2</sup><br>
        <hr>
        <b>Voimassa olevia lupia</b>: ${props.permitCount || 0}<br>
        `);
};

function getKeyForAreas(areas: PermitArea[]): string {
    const countSum = areas.reduce(
        (sum, a) => sum + (a.properties?.permitCount || 0), 0);
    return `${areas.length}/${countSum}`;
}

interface AreaCollection extends
geojson.FeatureCollection<geojson.MultiPolygon, PermitAreaProperties> {
    features: Array<PermitArea>;
}

function getFeatureCollection(areas: PermitArea[]): AreaCollection {
    return {type: 'FeatureCollection', features: areas};
}

function getStyleForArea(area: any) {
    const count: number = area.properties?.permitCount || 0;
    return {
        dashArray: '3',
        weight: 1,
        color: '#000000',
        opacity: 0.6,
        fillColor: '#1565c0',
        fillOpacity: count ? 0.25 + Math.min(count / 100, 1) / 2 : 0.05,
    };
}
