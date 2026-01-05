import * as axios from 'axios';
import { Moment } from 'moment';

import AuthManager from './auth-manager';
import { ParkingList, RegionList, RegionStatsList } from './types';

interface SuccessCallback<T> {
    (response: axios.AxiosResponse<T>): void;
}

interface ErrorHandler {
    (error: axios.AxiosError): void;
}

export class Api {
    public baseUrl: string | undefined;
    public endpoints = {
        authCheck: '/auth/v1/check/',
        regions: '/monitoring/v1/region/',
        regionStats: '/monitoring/v1/region_statistics/',
        validParkings: '/monitoring/v1/valid_parking/',
    };

    public auth: AuthManager;

    private axios: axios.AxiosInstance;

    constructor(baseUrl?: string) {
        this.baseUrl = baseUrl;
        this.axios = axios.default.create({
            baseURL: baseUrl,
            withCredentials: true, // Required for session-based authentication
        });
        this.auth = new AuthManager(this, this.axios);
    }

    setBaseUrl(baseUrl: string) {
        this.baseUrl = baseUrl;
        this.axios.defaults.baseURL = baseUrl;
    }

    fetchRegions(
        callback: SuccessCallback<RegionList>,
        errorHandler: ErrorHandler
    ) {
        this._fetchAllPages(this.endpoints.regions, callback, errorHandler);
    }

    fetchRegionStats(
        time: Moment,
        callback: SuccessCallback<RegionStatsList>,
        errorHandler: ErrorHandler
    ) {
        const timeParam = (time) ? '?time=' + time.toISOString() : '';
        this._fetchAllPages(this.endpoints.regionStats + timeParam,
                            callback, errorHandler);
    }

    fetchValidParkings(
        time: Moment,
        callback: SuccessCallback<ParkingList>,
        errorHandler: ErrorHandler,
    ): void {
        const timeParam = (time) ? '?time=' + time.toISOString() : '';
        this._fetchAllPages(this.endpoints.validParkings + timeParam,
                            callback, errorHandler);
    }

    private _fetchAllPages(
        url: string,
        callback: SuccessCallback<RegionList> | SuccessCallback<ParkingList> | SuccessCallback<RegionStatsList>,
        errorHandler: ErrorHandler
    ) {
        this.axios.get(url, { withCredentials: true })
            .then((response) => {
                callback(response);
                const nextUrl = response.data.next;
                if (nextUrl) {
                    this._fetchAllPages(nextUrl, callback, errorHandler);
                }
            })
            .catch(errorHandler);
    }
}

const api = new Api();

export default api;
