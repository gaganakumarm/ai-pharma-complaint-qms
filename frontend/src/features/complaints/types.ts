export type ProductType = 'API' | 'FDF' | 'UNKNOWN'
export type ComplaintSeverity = '' | 'MINOR' | 'MAJOR' | 'CRITICAL'

export interface ComplaintDraft {
  complaintSource: string
  customerName: string
  productType: ProductType
  productName: string
  productStrengthGrade: string
  batchLotNumber: string
  affectedQuantity: string
  manufacturingDate: string
  expiryRetestDate: string
  originatingSiteBlock: string
  impactedNonProductMaterials: string
  complaintCategory: string
  complaintDescription: string
  suggestedSeverity: ComplaintSeverity
  initialRiskAssessment: string
  suggestedNextAction: string
}

export interface ComplaintRecord {
  id: string
  complaint_number: string
  source_type: 'MANUAL' | 'TEXT' | 'PDF'
  complaint_source: string | null
  customer_name: string
  product_type: ProductType
  product_name: string
  product_strength_grade: string | null
  batch_lot_number: string
  affected_quantity: string | null
  manufacturing_date: string | null
  expiry_retest_date: string | null
  originating_site_block: string | null
  impacted_non_product_materials: string | null
  complaint_category: string
  complaint_description: string
  suggested_severity: Exclude<ComplaintSeverity, ''> | null
  initial_risk_assessment: string | null
  suggested_next_action: string | null
  status: 'COMMITTED'
  raw_input: null
  created_at: string
  updated_at: string
}

export interface ExtractedComplaint {
  complaint_source: string | null
  customer_name: string | null
  product_type: ProductType | null
  product_name: string | null
  product_strength_grade: string | null
  batch_lot_number: string | null
  affected_quantity: string | null
  manufacturing_date: string | null
  expiry_retest_date: string | null
  originating_site_block: string | null
  impacted_non_product_materials: string | null
  complaint_description: string | null
}

export interface ProcessTextResponse {
  source_type: 'TEXT'
  input_length: number
  extracted_complaint: ExtractedComplaint
  quality_assessment: ComplaintQualityAssessment
  warnings: string[]
  assistant_message: string
  status: 'PROCESSED'
  model: string
}

export interface SelectedDocument {
  name: string
  size: number
  type: string
}

export interface DocumentMetadata {
  filename: string
  content_type: string
  page_count: number
  character_count: number
}

export interface ProcessDocumentResponse {
  source_type: 'PDF'
  document: DocumentMetadata
  extracted_complaint: ExtractedComplaint
  quality_assessment: ComplaintQualityAssessment
  warnings: string[]
  assistant_message: string
  status: 'PROCESSED'
  model: string
}

export interface ComplaintQualityAssessment {
  complaint_category: string
  structured_complaint_description: string
  suggested_severity: Exclude<ComplaintSeverity, ''>
  severity_rationale: string
  initial_risk_assessment: string
  suggested_next_action: string
  assessment_status: 'COMPLETE' | 'NEEDS_INFORMATION'
  information_gaps: string[]
  human_review_required: true
  disclaimer: string
}

export interface ConversationMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
}

export type CorrectionField = keyof ExtractedComplaint | 'complaint_category'

export interface CorrectableComplaint extends ExtractedComplaint {
  complaint_category: string | null
}

export interface ComplaintCorrectionResponse {
  patch: {
    updates: { field: CorrectionField; value: string | null }[]
    clarification_required: boolean
    clarification_question: string | null
  }
  updated_complaint: CorrectableComplaint
  changed_fields: CorrectionField[]
  warnings: string[]
  quality_assessment: ComplaintQualityAssessment
  assistant_message: string
  status: 'APPLIED' | 'CLARIFICATION_REQUIRED' | 'NO_CHANGES'
  model: string
}
