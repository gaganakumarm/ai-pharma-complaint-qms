import { apiClient } from '../../shared/api/client'
import type {
  ComplaintDraft,
  ComplaintRecord,
  ProcessTextResponse,
  ProcessDocumentResponse,
  ComplaintQualityAssessment,
  ComplaintCorrectionResponse,
  CompletenessAssessment,
  DuplicateMatch,
  RcaCapaRecommendations,
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

export async function correctComplaint(
  draft: ComplaintDraft,
  assessment: ComplaintQualityAssessment,
  instruction: string,
  completeness: CompletenessAssessment | null = null,
  duplicates: DuplicateMatch[] = [],
  rcaCapa: RcaCapaRecommendations | null = null,
) {
  const response = await apiClient.post<ComplaintCorrectionResponse>(
    '/api/complaints/correct',
    {
      current_complaint: {
        complaint_source: optional(draft.complaintSource),
        customer_name: optional(draft.customerName),
        product_type: draft.productType,
        product_name: optional(draft.productName),
        product_strength_grade: optional(draft.productStrengthGrade),
        batch_lot_number: optional(draft.batchLotNumber),
        affected_quantity: optional(draft.affectedQuantity),
        manufacturing_date: optional(draft.manufacturingDate),
        expiry_retest_date: optional(draft.expiryRetestDate),
        originating_site_block: optional(draft.originatingSiteBlock),
        impacted_non_product_materials: optional(
          draft.impactedNonProductMaterials,
        ),
        complaint_category: optional(draft.complaintCategory),
        complaint_description: optional(draft.complaintDescription),
      },
      instruction,
      current_quality_assessment: assessment,
      current_completeness_assessment: completeness,
      current_possible_duplicate_matches: duplicates,
      current_rca_capa_recommendations: rcaCapa,
    },
  )
  return response.data
}

const optional = (value: string) => value.trim() || null

export async function commitComplaint(
  draft: ComplaintDraft,
  sourceType: 'MANUAL' | 'TEXT' | 'PDF' = 'MANUAL',
) {
  const response = await apiClient.post<ComplaintRecord>('/api/complaints', {
    source_type: sourceType,
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

export async function processComplaintDocument(file: File) {
  const formData = new FormData()
  formData.append('file', file)
  const response = await apiClient.post<ProcessDocumentResponse>(
    '/api/complaints/process-document',
    formData,
  )
  return response.data
}
