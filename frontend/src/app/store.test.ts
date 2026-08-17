import { describe, expect, it } from 'vitest'

import { store } from './store'

describe('Redux store', () => {
  it('initializes the application state', () => {
    expect(store.getState().app.initialized).toBe(true)
  })
})
