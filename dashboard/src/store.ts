import {
  applyMiddleware,
  compose,
  createStore,
  Store,
  Middleware,
} from 'redux';
import thunk from 'redux-thunk';

import { createLogger } from 'redux-logger';
import { RootState } from './types';
import rootReducer from './reducers';
import * as config from './config';

const middlewares: Middleware[] = [thunk];
if (config.isDev) {
  middlewares.push(createLogger() as any);
}

const composeEnhancers = (process.env.NODE_ENV === 'development'
    && window
    && (window as any).__REDUX_DEVTOOLS_EXTENSION_COMPOSE__)
  || compose;

export default function initStore(): Store<RootState> {
  return createStore(
    rootReducer(),
    composeEnhancers(
      applyMiddleware(...middlewares),
    ),
  );
}
