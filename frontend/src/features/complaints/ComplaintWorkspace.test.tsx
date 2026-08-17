import { act, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Provider } from 'react-redux'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { createAppStore } from '../../app/store'
import { commitComplaint } from './api'
import { commitComplaintDraft } from './complaintSlice'
import { ComplaintWorkspace } from './ComplaintWorkspace'
import type { ComplaintRecord } from './types'

vi.mock('./api', () => ({ commitComplaint: vi.fn() }))
const mockedCommit = vi.mocked(commitComplaint)

const savedRecord: ComplaintRecord = {
  id: '9bf66d1e-69cb-4e9c-ae66-ff74878d3666',
  complaint_number: 'CMP-2026-000001',
  source_type: 'MANUAL',
  complaint_source: null,
  customer_name: 'Acme Hospital',
  product_type: 'FDF',
  product_name: 'Paracetamol',
  product_strength_grade: null,
  batch_lot_number: 'LOT-1',
  affected_quantity: null,
  manufacturing_date: null,
  expiry_retest_date: null,
  originating_site_block: null,
  impacted_non_product_materials: null,
  complaint_category: 'Packaging',
  complaint_description: 'Damaged seal',
  suggested_severity: null,
  initial_risk_assessment: null,
  suggested_next_action: null,
  status: 'COMMITTED',
  raw_input: null,
  created_at: '2026-08-17T00:00:00Z',
  updated_at: '2026-08-17T00:00:00Z',
}

function renderWorkspace() {
  const store = createAppStore()
  render(
    <Provider store={store}>
      <ComplaintWorkspace />
    </Provider>,
  )
  return store
}

async function fillRequired(user: ReturnType<typeof userEvent.setup>) {
  await user.type(screen.getByLabelText(/Customer Name/), 'Acme Hospital')
  await user.type(screen.getByLabelText(/Product Name/), 'Paracetamol')
  await user.type(screen.getByLabelText(/Batch\/Lot Number/), 'LOT-1')
  await user.type(screen.getByLabelText(/Complaint Category/), 'Packaging')
  await user.type(
    screen.getByLabelText(/Complaint Description/),
    'Damaged seal',
  )
}

describe('ComplaintWorkspace', () => {
  beforeEach(() => mockedCommit.mockReset())

  it('renders the complete form and accessible validation', async () => {
    const user = userEvent.setup()
    renderWorkspace()
    expect(screen.getByText('Origin and Customer Details')).toBeInTheDocument()
    expect(screen.getByText('AI Copilot Risk Assessment')).toBeInTheDocument()
    const customer = screen.getByLabelText(/Customer Name/)
    await user.type(customer, 'x')
    await user.clear(customer)
    expect(
      await screen.findByText('Customer name is required'),
    ).toBeInTheDocument()
    expect(screen.getByText('Pending Triage')).toBeInTheDocument()
  })

  it('updates Redux and reaches Ready to Commit', async () => {
    const user = userEvent.setup()
    const store = renderWorkspace()
    await fillRequired(user)
    expect(store.getState().complaint.draft.batchLotNumber).toBe('LOT-1')
    expect(await screen.findByText('Ready to Commit')).toBeInTheDocument()
  })

  it('commits once and displays the committed record', async () => {
    mockedCommit.mockResolvedValue(savedRecord)
    const user = userEvent.setup()
    renderWorkspace()
    await fillRequired(user)
    const button = screen.getByRole('button', { name: 'Commit to QMS Ledger' })
    await user.click(button)
    expect(await screen.findByText('CMP-2026-000001')).toBeInTheDocument()
    expect(screen.getAllByText('COMMITTED')).toHaveLength(1)
    expect(mockedCommit).toHaveBeenCalledTimes(1)
    expect(button).toBeDisabled()
    button.click()
    expect(mockedCommit).toHaveBeenCalledTimes(1)
  })

  it('preserves values after failure and reset clears them', async () => {
    const user = userEvent.setup()
    const store = renderWorkspace()
    await fillRequired(user)
    act(() => {
      store.dispatch(
        commitComplaintDraft.rejected(
          new Error('Network unavailable'),
          'test-request',
          store.getState().complaint.draft,
        ),
      )
    })
    expect(await screen.findByText(/Network unavailable/)).toBeInTheDocument()
    expect(screen.getByLabelText(/Customer Name/)).toHaveValue('Acme Hospital')
    await user.click(screen.getByRole('button', { name: 'Reset Form' }))
    await waitFor(() =>
      expect(screen.getByLabelText(/Customer Name/)).toHaveValue(''),
    )
    expect(screen.getByText('Pending Triage')).toBeInTheDocument()
  })
})
