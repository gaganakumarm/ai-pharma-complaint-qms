import { apiClient } from '../../shared/api/client'
import type {
  ComplaintDraft,
  ComplaintRecord,
  ProcessTextResponse,
} from './types'

export interface PaginatedComplaints {
  items: Array<
    Pick<
      ComplaintRecord,
      | 'id'
      | 'complaint_number'
      | 'customer_name'
      | 'product_name'
      | 'batch_lot_number'
      | 'complaint_category'
      | 'status'
      | 'created_at'
    >
  >
  page: number
  page_size: number
  total: number
  total_pages: number
}

const optional = (value: string) => value.trim() || null

export async function commitComplaint(draft: ComplaintDraft) {
  const response = await apiClient.post<ComplaintRecord>('/api/complaints', {
    source_type: 'MANUAL',
    complaint_source: optional(draft.complaintSource),
    customer_name: draft.customerName.trim(),
    product_type: draft.productType,
    product_name: draft.productName.trim(),
    product_strength_grade: optional(draft.productStrengthGrade),
    batch_lot_number: draft.batchLotNumber.trim(),
    affected_quantity: optional(draft.affectedQuantity),
    manufacturing_date: optional(draft.manufacturingDate),
    expiry_retest_date: optional(draft.expiryRetestDate),
    originating_site_block: optional(draft.originatingSiteBlock),
    impacted_non_product_materials: optional(draft.impactedNonProductMaterials),
    complaint_category: draft.complaintCategory.trim(),
    complaint_description: draft.complaintDescription.trim(),
    suggested_severity: draft.suggestedSeverity || null,
    initial_risk_assessment: optional(draft.initialRiskAssessment),
    suggested_next_action: optional(draft.suggestedNextAction),
  })
  return response.data
}

export async function getComplaint(complaintId: string) {
  const response = await apiClient.get<ComplaintRecord>(
    `/api/complaints/${complaintId}`,
  )
  return response.data
}

export async function listComplaints(page = 1, pageSize = 20) {
  const response = await apiClient.get<PaginatedComplaints>('/api/complaints', {
    params: { page, page_size: pageSize },
  })
  return response.data
}

export async function processComplaintText(text: string) {
  const response = await apiClient.post<ProcessTextResponse>(
    '/api/complaints/process-text',
    { text },
  )
  return response.data
}
