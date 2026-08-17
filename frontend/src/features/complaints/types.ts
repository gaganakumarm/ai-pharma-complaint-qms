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
  source_type: 'MANUAL'
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
