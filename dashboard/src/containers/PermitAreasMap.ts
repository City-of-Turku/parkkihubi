import * as _ from 'lodash';
import { connect } from 'react-redux';

import PermitAreasMap, { Props } from '../components/PermitAreasMap';
import { PermitArea } from '../components/types';
import { RootState } from '../types';

const mapStateToProps = (state: RootState): Props => {
    const {dataTime, permitAreas, permitCountHistory} = state;
    const counts = (dataTime != null && permitCountHistory[dataTime]) || {};
    const areas = _.values(permitAreas).map((area: PermitArea): PermitArea => ({
        ...area,
        properties: {...area.properties, permitCount: counts[area.id] || 0},
    }));
    const viewState = state.views.parkingRegionMap;
    return {center: viewState.center, zoom: viewState.zoom, areas};
};

export default connect(mapStateToProps)(PermitAreasMap);
