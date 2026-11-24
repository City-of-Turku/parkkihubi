import { Component } from 'react';
import { connect } from 'react-redux';

import { Button, ButtonGroup } from 'react-bootstrap';

import RegionSelector from './RegionSelector';
import * as dispatchers from '../dispatchers';
import { DashboardTab, RootState } from '../types';

import './Dashboard.css';
import TimeSelect from '../containers/TimeSelect';
import ParkingRegionsMap from './ParkingRegionsMap';
import LastParkingsTable from './LastParkingsTable';
import PermitAreasMap from './PermitAreasMap';
import PermitAreasTable from './PermitAreasTable';

interface Props {
    autoUpdate?: boolean;
    activeTab?: DashboardTab;
    onTabChange?: (tab: DashboardTab) => void;
    onUpdate?: () => void;
    onLogout?: () => void;
}


const tabs: Array<[DashboardTab, string]> = [
    ['parkings', 'Aktiiviset pysäköinnit'],
    ['permits', 'Lupapysäköinnit'],
];

class Dashboard extends Component<Props> {
    timer: number|null = null;

    timerInterval: number = 1000; // 1 second

    componentDidMount() {
      if (this.props.autoUpdate && !this.timer) {
        this.enableAutoUpdate();
      }
    }

    // eslint-disable-next-line camelcase
    UNSAFE_componentWillReceiveProps(nextProps: Props) {
      if (nextProps.autoUpdate && !this.timer) {
        this.enableAutoUpdate();
      }
      if (!nextProps.autoUpdate && this.timer) {
        this.disableAutoUpdate();
      }
    }

    enableAutoUpdate = () => {
      if (this.timer) {
        return; // Was already enabled
      }
      this.timer = setInterval(this.autoUpdate, this.timerInterval);
    }

    disableAutoUpdate = () => {
      if (!this.timer) {
        return; // Was already disabled
      }
      clearInterval(this.timer);
      this.timer = null;
    }

    autoUpdate = () => {
      if (this.props.onUpdate) {
        this.props.onUpdate();
      }
    }

    render() {
      const activeTab = this.props.activeTab || 'parkings';
      return (
        <main className="main d-flex flex-column">
            <div className="toolbar margin-bottom-8">
              <div className="d-flex align-items-center justify-content-center">
                  <img className="logo mini" src="parkkihubi.svg" alt=""/>
                  <h2>Parkkihubi</h2>
              </div>
              <Button
                  className="submit-button d-flex align-items-center"
                  onClick={this.props.onLogout}
                  variant="danger"
              >
                  <span>Kirjaudu ulos</span>
                  <i className="fa fa-sign-out" />
              </Button>
            </div>
            <ButtonGroup className="margin-bottom-8">
              {tabs.map(([tab, label]) => (
                <Button
                    key={tab}
                    variant={activeTab === tab ? 'primary' : 'outline-primary'}
                    onClick={() => this.props.onTabChange?.(tab)}
                >
                    {label}
                </Button>
              ))}
            </ButtonGroup>
            <div className="d-flex">
                <div className="table-card">
                    <TimeSelect />
                    <div className="margin-bottom-8" />
                    {activeTab === 'permits'
                        ? <PermitAreasTable />
                        : <LastParkingsTable />}
                </div>

                <div style={{width: '16px'}}/>

                <div className="map-card">
                    {activeTab === 'permits' ? <PermitAreasMap /> : (
                      <>
                        <RegionSelector />
                        <div className="margin-bottom-8" />
                        <ParkingRegionsMap/>
                      </>
                    )}
                </div>
            </div>
        </main>
      );
    }
}

const mapStateToProps = (state: RootState): Props => ({
  autoUpdate: state.autoUpdate,
  activeTab: state.activeTab,
});

const mapDispatchToProps = (dispatch: any): Props => ({
  onUpdate: () => dispatch(dispatchers.updateData()),
  onLogout: () => dispatch(dispatchers.logout()),
  onTabChange: (tab: DashboardTab) => dispatch(dispatchers.setActiveTab(tab)),
});

export default connect(mapStateToProps, mapDispatchToProps)(Dashboard);
