import { configureStore } from '@reduxjs/toolkit';
import { createLogger } from 'redux-logger';
import rootReducer from './reducers';
import * as config from './config';

export default function initStore() {
  const middlewareList: any[] = [];
  
  if (config.isDev) {
    middlewareList.push(createLogger());
  }

  return configureStore({
    reducer: rootReducer(),
    middleware: (getDefaultMiddleware) =>
      getDefaultMiddleware().concat(middlewareList),
    devTools: import.meta.env.MODE === 'development',
  });
}
