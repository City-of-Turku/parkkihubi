import { AxiosInstance } from 'axios';

import { Api } from './index';
import { AuthToken } from './types';

export default class AuthManager {
    private _api: Api;
    private _axios: AxiosInstance;

    constructor(api: Api, axiosInstance: AxiosInstance) {
        this._api = api;
        this._axios = axiosInstance;
        // Configure axios to send cookies with requests (required for session auth)
        this._axios.defaults.withCredentials = true;
    }

    /**
     * Check if user is authenticated via session.
     * Returns AuthToken if authenticated, null otherwise.
     */
    checkExistingLogin(): Promise<AuthToken|null> {
        // Check authentication status via a simple API call
        // The endpoint should return 200 if authenticated, 401/403 if not
        return this._axios.get(this._api.endpoints.authCheck, { withCredentials: true })
            .then((response) => {
                // User is authenticated - return a dummy token object
                // (we don't actually need the token for session auth)
                if (response.data && response.data.authenticated) {
                    return { token: 'session' } as AuthToken;
                }
                return null;
            })
            .catch((error) => {
                // User is not authenticated or CORS/network error
                // Log error for debugging (but don't expose to user)
                if (error.response) {
                    // Server responded with error status (401, 403, etc.)
                    // This means user is not authenticated
                    return null;
                } else if (error.request) {
                    // Request was made but no response received (network/CORS error)
                    console.error('Auth check failed - network error:', error.message);
                    // Return null to trigger login flow
                    return null;
                } else {
                    // Something else happened
                    console.error('Auth check failed:', error.message);
                    return null;
                }
            });
    }

    /**
     * Logout by redirecting to Tunnistamo logout endpoint
     */
    logout() {
        // Redirect to Tunnistamo logout
        const baseUrl = this._api.baseUrl || '';
        const logoutUrl = `${baseUrl}logout/`;
        window.location.href = logoutUrl;
    }
}
