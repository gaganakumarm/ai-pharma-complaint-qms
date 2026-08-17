import { configureStore } from '@reduxjs/toolkit'

import { complaintReducer } from '../features/complaints/complaintSlice'

export const createAppStore = () =>
  configureStore({ reducer: { complaint: complaintReducer } })
export const store = createAppStore()

export type RootState = ReturnType<typeof store.getState>
export type AppDispatch = typeof store.dispatch
