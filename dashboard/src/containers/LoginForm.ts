import { connect } from 'react-redux';

import LoginForm from '../components/LoginForm';
import { RootState } from '../types';

// No props needed - LoginForm handles Tunnistamo redirect directly
const mapStateToProps = (_state: RootState) => ({});

const mapDispatchToProps = () => ({});

export default connect(mapStateToProps, mapDispatchToProps)(LoginForm);
