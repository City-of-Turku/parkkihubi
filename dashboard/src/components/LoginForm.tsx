import * as React from 'react';
import { Button } from 'react-bootstrap';
import * as config from '../config';

export interface Props {
    // No longer needed - using Tunnistamo redirect
}

export interface State {
    // No longer needed - using Tunnistamo redirect
}

export default class LoginForm extends React.Component<Props, State> {
  handleTunnistamoLogin = () => {
    // Redirect to custom login endpoint that preserves 'next' parameter
    // This endpoint stores 'next' in session and redirects to admin login
    const returnUrl = encodeURIComponent(window.location.origin + window.location.pathname);
    const loginUrl = `${config.apiBaseUrl}login/?next=${returnUrl}`;
    window.location.href = loginUrl;
  }

  render() {
    return (
      <div className="d-flex flex-column align-items-center">
        <p className="mb-4">Kirjaudu sisään Turun kaupungin työntekijän tunnuksella:</p>
        <Button
          onClick={this.handleTunnistamoLogin}
          variant="primary"
          size="lg"
          className="submit-button d-flex align-items-center"
        >
          <span>Turku Login</span>
          <i className="fa fa-sign-in ms-2" />
        </Button>
      </div>
    );
  }
}
