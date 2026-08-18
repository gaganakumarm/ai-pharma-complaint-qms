import { render, screen } from '@testing-library/react'

import { EnhancementPanels } from './EnhancementPanels'

const completeness = {
  status: 'NEEDS_INFORMATION' as const,
  required_fields_present: 4,
  total_required_fields: 5,
  completeness_percentage: 80,
  missing_required_fields: ['batch_lot_number'],
  missing_recommended_fields: ['affected_quantity'],
  guidance: 'Provide the missing batch information.',
}

const rcaCapa = {
  potential_root_causes: [
    {
      statement: 'Packaging exposure may have contributed',
      rationale: 'Evidence is incomplete',
      evidence_required: 'Packaging integrity data',
    },
  ],
  investigation_areas: ['Packaging integrity'],
  corrective_actions: [
    {
      action: 'Evaluate containment',
      purpose: 'Protect product',
      verification: 'QA review',
    },
  ],
  preventive_actions: [
    {
      action: 'Trend findings',
      purpose: 'Detect recurrence',
      effectiveness_check: 'Periodic QA review',
    },
  ],
  assumptions_or_limitations: ['Causality is not established'],
  human_review_required: true as const,
  disclaimer: 'Trusted application disclaimer',
}

test('renders completeness, ranked duplicate, RCA/CAPA, and stale guidance', () => {
  render(
    <EnhancementPanels
      completeness={completeness}
      duplicates={[
        {
          complaint_id: '00000000-0000-0000-0000-000000000001',
          complaint_number: 'CMP-2026-000001',
          product_name: 'Amoxicillin Capsules',
          batch_lot_number: 'LOT-1',
          complaint_category: 'Discoloration',
          status: 'COMMITTED',
          created_at: '2026-01-01T00:00:00Z',
          similarity_score: 91,
          match_level: 'STRONG_MATCH',
          match_reasons: ['Exact normalized batch/lot match'],
        },
      ]}
      rcaCapa={rcaCapa}
      stale
    />,
  )
  expect(screen.getByText(/NEEDS INFORMATION — 80%/)).toBeInTheDocument()
  expect(screen.getByText(/CMP-2026-000001 — 91%/)).toBeInTheDocument()
  expect(screen.getByText(/Possible match only/)).toBeInTheDocument()
  expect(screen.getByText(/Packaging exposure/)).toBeInTheDocument()
  expect(screen.getByText(/Human review required/)).toBeInTheDocument()
  expect(screen.getAllByText(/Results may be outdated/)).toHaveLength(2)
})

test('renders the duplicate empty state', () => {
  render(
    <EnhancementPanels
      completeness={completeness}
      duplicates={[]}
      rcaCapa={rcaCapa}
      stale={false}
    />,
  )
  expect(screen.getByText('No possible matches found')).toBeInTheDocument()
})
