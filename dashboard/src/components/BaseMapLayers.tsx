import { ScaleControl, TileLayer } from 'react-leaflet';

import { mapTilesUrl } from '../config';

const attribution = (
    'Pohjakartta &copy; Turun kaupunki, '
    + '<a href="https://creativecommons.org/licenses/by/4.0/deed.fi">'
    + 'käyttölupa CC BY 4.0</a>'
    + ' | &copy; <a href="https://www.openstreetmap.org/copyright">'
    + 'OpenStreetMapin tekijät</a>');

export default function BaseMapLayers() {
    return (
        <>
            <TileLayer attribution={attribution} url={mapTilesUrl} />
            <ScaleControl metric={true} imperial={false} maxWidth={150}/>
        </>
    );
}
