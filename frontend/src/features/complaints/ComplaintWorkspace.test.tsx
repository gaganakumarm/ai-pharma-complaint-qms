import { act, fireEvent, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Provider } from 'react-redux'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { createAppStore } from '../../app/store'
import {
  commitComplaint,
  processComplaintDocument,
  processComplaintText,
} from './api'
import { commitComplaintDraft, processTextComplaint } from './complaintSlice'
import { ComplaintWorkspace } from './ComplaintWorkspace'
import type { ComplaintRecord } from './types'

vi.mock('./api', () => ({
  commitComplaint: vi.fn(),
  processComplaintDocument: vi.fn(),
  processComplaintText: vi.fn(),
}))
const mockedCommit = vi.mocked(commitComplaint)
const mockedProcess = vi.mocked(processComplaintText)
const mockedProcessDocument = vi.mocked(processComplaintDocument)

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
  beforeEach(() => {
    mockedCommit.mockReset()
    mockedProcess.mockReset()
    mockedProcessDocument.mockReset()
  })

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

  it('prevents blank processing and populates extracted fields', async () => {
    mockedProcess.mockResolvedValue({
      source_type: 'TEXT',
      input_length: 44,
      status: 'PROCESSED',
      model: 'fake-model',
      warnings: [],
      assistant_message: 'Review the populated form.',
      extracted_complaint: {
        complaint_source: 'Email',
        customer_name: 'Apollo Pharmacy',
        product_type: 'FDF',
        product_name: 'Paracetamol',
        product_strength_grade: '500 mg',
        batch_lot_number: 'FDF-42',
        affected_quantity: null,
        manufacturing_date: null,
        expiry_retest_date: null,
        originating_site_block: null,
        impacted_non_product_materials: null,
        complaint_description: 'Cracked tablets.',
      },
    })
    const user = userEvent.setup()
    renderWorkspace()
    const button = screen.getByRole('button', { name: 'Process Complaint' })
    expect(button).toBeDisabled()
    await user.type(
      screen.getByLabelText('Complaint text or email'),
      'Apollo email complaint',
    )
    await user.click(button)
    expect(await screen.findByDisplayValue('Paracetamol')).toBeInTheDocument()
    expect(screen.getByDisplayValue('FDF-42')).toBeInTheDocument()
    expect(screen.getAllByText('Apollo email complaint')).toHaveLength(2)
    expect(screen.getByText('Review the populated form.')).toBeInTheDocument()
  })

  it('keeps existing values when extraction is null and shows warnings', async () => {
    mockedProcess.mockResolvedValue({
      source_type: 'TEXT',
      input_length: 20,
      status: 'PROCESSED',
      model: 'fake-model',
      warnings: ['Batch number was not provided'],
      assistant_message: 'Please add missing information.',
      extracted_complaint: {
        complaint_source: null,
        customer_name: null,
        product_type: null,
        product_name: null,
        product_strength_grade: null,
        batch_lot_number: null,
        affected_quantity: null,
        manufacturing_date: null,
        expiry_retest_date: null,
        originating_site_block: null,
        impacted_non_product_materials: null,
        complaint_description: 'Damaged product.',
      },
    })
    const user = userEvent.setup()
    renderWorkspace()
    await user.type(screen.getByLabelText(/Customer Name/), 'Existing Customer')
    await user.type(
      screen.getByLabelText('Complaint text or email'),
      'Incomplete complaint',
    )
    await user.click(screen.getByRole('button', { name: 'Process Complaint' }))
    expect(
      await screen.findByText('Batch number was not provided'),
    ).toBeInTheDocument()
    expect(screen.getByLabelText(/Customer Name/)).toHaveValue(
      'Existing Customer',
    )
    expect(screen.getByText('Pending Triage')).toBeInTheDocument()
  })

  it('preserves text on processing error and retries once', async () => {
    mockedProcess.mockResolvedValue({
      source_type: 'TEXT',
      input_length: 10,
      status: 'PROCESSED',
      model: 'fake-model',
      warnings: [],
      assistant_message: 'Processed after retry.',
      extracted_complaint: {
        complaint_source: null,
        customer_name: null,
        product_type: 'UNKNOWN',
        product_name: null,
        product_strength_grade: null,
        batch_lot_number: null,
        affected_quantity: null,
        manufacturing_date: null,
        expiry_retest_date: null,
        originating_site_block: null,
        impacted_non_product_materials: null,
        complaint_description: null,
      },
    })
    const user = userEvent.setup()
    const store = renderWorkspace()
    await user.type(
      screen.getByLabelText('Complaint text or email'),
      'Retry this text',
    )
    act(() => {
      store.dispatch(
        processTextComplaint.rejected(
          new Error('Provider unavailable'),
          'failed',
          'Retry this text',
        ),
      )
    })
    expect(await screen.findByText(/Provider unavailable/)).toBeInTheDocument()
    expect(screen.getByLabelText('Complaint text or email')).toHaveValue(
      'Retry this text',
    )
    await user.click(screen.getByRole('button', { name: 'Retry' }))
    expect(
      await screen.findByText('Processed after retry.'),
    ).toBeInTheDocument()
    expect(mockedProcess).toHaveBeenCalledTimes(1)
  })

  it('shows processing stages and prevents duplicate processing clicks', async () => {
    let resolveRequest:
      | ((value: Awaited<ReturnType<typeof processComplaintText>>) => void)
      | undefined
    mockedProcess.mockImplementation(
      () =>
        new Promise((resolve) => {
          resolveRequest = resolve
        }),
    )
    const user = userEvent.setup()
    renderWorkspace()
    await user.type(
      screen.getByLabelText('Complaint text or email'),
      'Pending extraction',
    )
    const button = screen.getByRole('button', { name: 'Process Complaint' })
    await user.dblClick(button)
    expect(
      await screen.findByText('Extracting product and batch information'),
    ).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Processing…' })).toBeDisabled()
    expect(mockedProcess).toHaveBeenCalledTimes(1)
    resolveRequest?.({
      source_type: 'TEXT',
      input_length: 18,
      status: 'PROCESSED',
      model: 'fake-model',
      warnings: [],
      assistant_message: 'Done.',
      extracted_complaint: {
        complaint_source: null,
        customer_name: null,
        product_type: null,
        product_name: null,
        product_strength_grade: null,
        batch_lot_number: null,
        affected_quantity: null,
        manufacturing_date: null,
        expiry_retest_date: null,
        originating_site_block: null,
        impacted_non_product_materials: null,
        complaint_description: null,
      },
    })
    expect(await screen.findByText('Done.')).toBeInTheDocument()
  })

  it('selects, displays, and removes a PDF accessibly', async () => {
    const user = userEvent.setup()
    renderWorkspace()
    const input = screen.getByLabelText('Choose a PDF or drag it here')
    const pdf = new File(['%PDF-test'], 'complaint.PDF', {
      type: 'application/pdf',
    })
    await user.upload(input, pdf)
    expect(screen.getByText('complaint.PDF')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Remove' }))
    expect(screen.queryByText('complaint.PDF')).not.toBeInTheDocument()
  })

  it('rejects unsupported and oversized files before a request', async () => {
    const user = userEvent.setup({ applyAccept: false })
    renderWorkspace()
    const input = screen.getByLabelText('Choose a PDF or drag it here')
    await user.upload(
      input,
      new File(['plain'], 'complaint.txt', { type: 'text/plain' }),
    )
    expect(
      screen.getByText(/Only PDF documents are supported/),
    ).toBeInTheDocument()
    const oversized = new File(
      [new Uint8Array(10 * 1024 * 1024 + 1)],
      'large.pdf',
      { type: 'application/pdf' },
    )
    await user.upload(input, oversized)
    expect(screen.getByText(/PDF must not exceed 10 MB/)).toBeInTheDocument()
    expect(mockedProcessDocument).not.toHaveBeenCalled()
  })

  it('accepts a dropped PDF and populates fields without erasing values', async () => {
    mockedProcessDocument.mockResolvedValue({
      source_type: 'PDF',
      document: {
        filename: 'api.pdf',
        content_type: 'application/pdf',
        page_count: 1,
        character_count: 100,
      },
      status: 'PROCESSED',
      model: 'fake-model',
      warnings: ['Affected quantity was not provided'],
      assistant_message: 'Review the PDF draft.',
      extracted_complaint: {
        complaint_source: null,
        customer_name: 'ABC Formulations Ltd.',
        product_type: 'API',
        product_name: 'Metformin Hydrochloride API',
        product_strength_grade: 'IP/BP',
        batch_lot_number: 'MET-API-77A',
        affected_quantity: null,
        manufacturing_date: null,
        expiry_retest_date: null,
        originating_site_block: null,
        impacted_non_product_materials: null,
        complaint_description: 'Foreign particles.',
      },
    })
    const user = userEvent.setup()
    renderWorkspace()
    await user.type(screen.getByLabelText(/Affected Quantity/), 'Existing qty')
    const pdf = new File(['%PDF-test'], 'api.pdf', { type: 'application/pdf' })
    fireEvent.drop(
      screen.getByText('Choose a PDF or drag it here').parentElement!,
      {
        dataTransfer: { files: [pdf] },
      },
    )
    await user.click(screen.getByRole('button', { name: 'Process PDF' }))
    expect(await screen.findByDisplayValue('MET-API-77A')).toBeInTheDocument()
    expect(screen.getByLabelText(/Affected Quantity/)).toHaveValue(
      'Existing qty',
    )
    expect(screen.getByText('Review the PDF draft.')).toBeInTheDocument()
    expect(
      screen.getByText('Affected quantity was not provided'),
    ).toBeInTheDocument()
  })

  it('prevents duplicate PDF submissions and preserves retry context', async () => {
    let rejectRequest: ((reason: Error) => void) | undefined
    mockedProcessDocument.mockImplementationOnce(
      () =>
        new Promise((_resolve, reject) => {
          rejectRequest = reject
        }),
    )
    const user = userEvent.setup()
    renderWorkspace()
    await user.upload(
      screen.getByLabelText('Choose a PDF or drag it here'),
      new File(['%PDF-test'], 'retry.pdf', { type: 'application/pdf' }),
    )
    const button = screen.getByRole('button', { name: 'Process PDF' })
    await user.dblClick(button)
    expect(
      await screen.findByText('Extracting selectable text'),
    ).toBeInTheDocument()
    expect(mockedProcessDocument).toHaveBeenCalledTimes(1)
    rejectRequest?.(new Error('PDF service unavailable'))
    expect(
      await screen.findByText(/PDF service unavailable/),
    ).toBeInTheDocument()
    expect(screen.getByText('retry.pdf')).toBeInTheDocument()
  })
})
