import * as _ from 'lodash';
import { connect } from 'react-redux';

import LastParkingsTable from '../components/LastParkingsTable';
import { RootState } from '../types';
import './LastParkingsTable.css';

const columns = [
    {
        attrs: { 'data-title': 'Tunnus' },
        text: 'Tunnus',
        dataField: 'identifier',
        headerStyle: { width: '120px' },
    }, {
        attrs: { 'data-title': 'Alue' },
        text: 'Alue',
        dataField: 'name',
    }, {
        attrs: { 'data-title': 'Pinta-ala (km²)' },
        text: 'Pinta-ala (km²)',
        dataField: 'areaKm2',
        formatter: (value: number) => value.toFixed(2),
    }, {
        attrs: { 'data-title': 'Voimassa olevat luvat' },
        text: 'Voimassa olevat luvat',
        dataField: 'permitCount',
    },
];

const mapStateToProps = (state: RootState) => {
    const {dataTime, permitAreas, permitCountHistory} = state;
    const counts = (dataTime != null && permitCountHistory[dataTime]) || {};
    const data = _.sortBy(
        _.values(permitAreas).map((area) => ({
            id: area.id,
            ...area.properties,
            permitCount: counts[area.id] || 0,
        })),
        (row) => -row.permitCount);
    return {data, columns, keyField: 'id'};
};

export default connect(mapStateToProps)(LastParkingsTable);
