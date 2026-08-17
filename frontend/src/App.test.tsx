import { render, screen } from '@testing-library/react'
import { Provider } from 'react-redux'
import { describe, expect, it } from 'vitest'

import { App } from './App'
import { store } from './app/store'

describe('App', () => {
  it('renders both Sprint 0 placeholders', () => {
    render(
      <Provider store={store}>
        <App />
      </Provider>,
    )

    expect(screen.getByText('Log Customer Complaint')).toBeInTheDocument()
    expect(screen.getByText('AIVOA Copilot')).toBeInTheDocument()
  })
})
