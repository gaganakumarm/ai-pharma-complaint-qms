import { createAsyncThunk, createSlice } from '@reduxjs/toolkit'

import {
  commitComplaint,
  processComplaintDocument,
  processComplaintText,
  correctComplaint,
} from './api'
import type {
  ComplaintDraft,
  ComplaintRecord,
  ConversationMessage,
  ExtractedComplaint,
  SelectedDocument,
  ComplaintQualityAssessment,
  CompletenessAssessment,
  DuplicateMatch,
  RcaCapaRecommendations,
} from './types'

export const initialDraft: ComplaintDraft = {
  complaintSource: '',
  customerName: '',
  productType: 'UNKNOWN',
  productName: '',
  productStrengthGrade: '',
  batchLotNumber: '',
  affectedQuantity: '',
  manufacturingDate: '',
  expiryRetestDate: '',
  originatingSiteBlock: '',
  impactedNonProductMaterials: '',
  complaintCategory: '',
  complaintDescription: '',
  suggestedSeverity: '',
  initialRiskAssessment: '',
  suggestedNextAction: '',
}

export interface ComplaintState {
  draft: ComplaintDraft
  sourceType: 'MANUAL' | 'TEXT' | 'PDF'
  requestStatus: 'idle' | 'saving' | 'succeeded' | 'failed'
  savedRecord: ComplaintRecord | null
  error: string | null
  copilotInput: string
  conversation: ConversationMessage[]
  processingStatus: 'idle' | 'processing' | 'succeeded' | 'failed'
  processingError: string | null
  warnings: string[]
  lastProcessedInputLength: number | null
  selectedDocument: SelectedDocument | null
  documentStatus:
    | 'idle'
    | 'selected'
    | 'uploading'
    | 'extracting'
    | 'analysing'
    | 'succeeded'
    | 'failed'
  documentError: string | null
  documentWarnings: string[]
  qualityAssessment: ComplaintQualityAssessment | null
  correctionInstruction: string
  correctionStatus:
    'idle' | 'processing' | 'succeeded' | 'clarification_required' | 'failed'
  correctionError: string | null
  changedFields: string[]
  clarificationQuestion: string | null
  completenessAssessment: CompletenessAssessment | null
  possibleDuplicateMatches: DuplicateMatch[]
  rcaCapaRecommendations: RcaCapaRecommendations | null
  enhancementResultsStale: boolean
}

const initialState: ComplaintState = {
  draft: initialDraft,
  sourceType: 'MANUAL',
  requestStatus: 'idle',
  savedRecord: null,
  error: null,
  copilotInput: '',
  conversation: [],
  processingStatus: 'idle',
  processingError: null,
  warnings: [],
  lastProcessedInputLength: null,
  selectedDocument: null,
  documentStatus: 'idle',
  documentError: null,
  documentWarnings: [],
  qualityAssessment: null,
  correctionInstruction: '',
  correctionStatus: 'idle',
  correctionError: null,
  changedFields: [],
  clarificationQuestion: null,
  completenessAssessment: null,
  possibleDuplicateMatches: [],
  rcaCapaRecommendations: null,
  enhancementResultsStale: false,
}

export const applyCorrection = createAsyncThunk(
  'complaint/correct',
  async (instruction: string, { getState, rejectWithValue }) => {
    const state = (getState() as { complaint: ComplaintState }).complaint
    if (!state.qualityAssessment)
      return rejectWithValue('Process a complaint first')
    try {
      return await correctComplaint(
        state.draft,
        state.qualityAssessment,
        instruction,
        state.completenessAssessment,
        state.possibleDuplicateMatches,
        state.rcaCapaRecommendations,
      )
    } catch (error) {
      return rejectWithValue(
        typeof error === 'object' && error !== null && 'message' in error
          ? String(error.message)
          : 'Unable to apply correction',
      )
    }
  },
  {
    condition: (_instruction, { getState }) =>
      (getState() as { complaint: ComplaintState }).complaint
        .correctionStatus !== 'processing',
  },
)

function applyAssessment(
  state: ComplaintState,
  assessment: ComplaintQualityAssessment,
) {
  state.qualityAssessment = assessment
  state.draft.complaintCategory = assessment.complaint_category
  state.draft.complaintDescription = assessment.structured_complaint_description
  state.draft.suggestedSeverity = assessment.suggested_severity
  state.draft.initialRiskAssessment = assessment.initial_risk_assessment
  state.draft.suggestedNextAction = assessment.suggested_next_action
}

function beginNewIntake(state: ComplaintState) {
  state.correctionInstruction = ''
  state.correctionStatus = 'idle'
  state.correctionError = null
  state.changedFields = []
  state.clarificationQuestion = null
  state.requestStatus = 'idle'
  state.savedRecord = null
  state.error = null
  state.completenessAssessment = null
  state.possibleDuplicateMatches = []
  state.rcaCapaRecommendations = null
  state.enhancementResultsStale = false
}

const requiredDraftFields: Array<keyof ComplaintDraft> = [
  'customerName',
  'productName',
  'batchLotNumber',
  'complaintCategory',
  'complaintDescription',
]
const placeholders = new Set([
  '',
  'n/a',
  'na',
  'none',
  'not applicable',
  'not available',
  'not provided',
  'unknown',
  'unavailable',
])
const fieldApiNames: Partial<Record<keyof ComplaintDraft, string>> = {
  customerName: 'customer_name',
  productName: 'product_name',
  batchLotNumber: 'batch_lot_number',
  complaintCategory: 'complaint_category',
  complaintDescription: 'complaint_description',
}
const relevantEnhancementFields = new Set<keyof ComplaintDraft>([
  'productType',
  'productName',
  'productStrengthGrade',
  'batchLotNumber',
  'affectedQuantity',
  'manufacturingDate',
  'expiryRetestDate',
  'originatingSiteBlock',
  'impactedNonProductMaterials',
  'complaintCategory',
  'complaintDescription',
  'suggestedSeverity',
  'initialRiskAssessment',
])

function meaningful(value: string) {
  return !placeholders.has(value.trim().toLowerCase().replace(/\.$/, ''))
}

function recalculateCompleteness(state: ComplaintState) {
  const missing = requiredDraftFields.filter(
    (field) => !meaningful(state.draft[field]),
  )
  const present = requiredDraftFields.length - missing.length
  const recommended: Array<[keyof ComplaintDraft, string]> = [
    ['complaintSource', 'complaint_source'],
    ['affectedQuantity', 'affected_quantity'],
    ['manufacturingDate', 'manufacturing_date'],
    ['expiryRetestDate', 'expiry_retest_date'],
    ['originatingSiteBlock', 'originating_site_block'],
    ['impactedNonProductMaterials', 'impacted_non_product_materials'],
  ]
  if (state.draft.productType === 'FDF' || state.draft.productType === 'API')
    recommended.push(['productStrengthGrade', 'product_strength_grade'])
  state.completenessAssessment = {
    status: missing.length ? 'NEEDS_INFORMATION' : 'COMPLETE',
    required_fields_present: present,
    total_required_fields: requiredDraftFields.length,
    completeness_percentage: Math.floor(
      (present * 100) / requiredDraftFields.length,
    ),
    missing_required_fields: missing.map((field) => fieldApiNames[field]!),
    missing_recommended_fields: recommended
      .filter(([field]) => !meaningful(state.draft[field]))
      .map(([, name]) => name),
    guidance: missing.length
      ? 'Provide the missing required information before manual commit.'
      : 'All required commit fields are present. Review recommended gaps and the full draft before manual commit.',
  }
}

function applyEnhancements(
  state: ComplaintState,
  payload: {
    completeness_assessment?: CompletenessAssessment
    possible_duplicate_matches?: DuplicateMatch[]
    rca_capa_recommendations?: RcaCapaRecommendations
  },
) {
  if (!payload.completeness_assessment || !payload.rca_capa_recommendations)
    return
  state.completenessAssessment = payload.completeness_assessment
  state.possibleDuplicateMatches = payload.possible_duplicate_matches ?? []
  state.rcaCapaRecommendations = payload.rca_capa_recommendations
  state.enhancementResultsStale = false
}

export const processDocumentComplaint = createAsyncThunk(
  'complaint/processDocument',
  async (file: File, { rejectWithValue }) => {
    try {
      return await processComplaintDocument(file)
    } catch (error) {
      const message =
        typeof error === 'object' && error !== null && 'message' in error
          ? String(error.message)
          : 'Unable to process PDF complaint'
      return rejectWithValue(message)
    }
  },
  {
    condition: (_file, { getState }) => {
      const status = (getState() as { complaint: ComplaintState }).complaint
        .documentStatus
      return !['uploading', 'extracting', 'analysing'].includes(status)
    },
  },
)

export const processTextComplaint = createAsyncThunk(
  'complaint/processText',
  async (text: string, { rejectWithValue }) => {
    try {
      return await processComplaintText(text)
    } catch (error) {
      const message =
        typeof error === 'object' && error !== null && 'message' in error
          ? String(error.message)
          : 'Unable to process complaint text'
      return rejectWithValue(message)
    }
  },
  {
    condition: (_text, { getState }) =>
      (getState() as { complaint: ComplaintState }).complaint
        .processingStatus !== 'processing',
  },
)

const extractionMap: Record<keyof ExtractedComplaint, keyof ComplaintDraft> = {
  complaint_source: 'complaintSource',
  customer_name: 'customerName',
  product_type: 'productType',
  product_name: 'productName',
  product_strength_grade: 'productStrengthGrade',
  batch_lot_number: 'batchLotNumber',
  affected_quantity: 'affectedQuantity',
  manufacturing_date: 'manufacturingDate',
  expiry_retest_date: 'expiryRetestDate',
  originating_site_block: 'originatingSiteBlock',
  impacted_non_product_materials: 'impactedNonProductMaterials',
  complaint_description: 'complaintDescription',
}

export const commitComplaintDraft = createAsyncThunk(
  'complaint/commit',
  async (draft: ComplaintDraft, { rejectWithValue, getState }) => {
    try {
      const sourceType = (getState() as { complaint: ComplaintState }).complaint
        .sourceType
      return await commitComplaint(draft, sourceType)
    } catch (error) {
      const message =
        typeof error === 'object' && error !== null && 'message' in error
          ? String(error.message)
          : 'Unable to commit complaint'
      return rejectWithValue(message)
    }
  },
  {
    condition: (_draft, { getState }) => {
      const state = getState() as { complaint: ComplaintState }
      return (
        state.complaint.requestStatus !== 'saving' &&
        state.complaint.requestStatus !== 'succeeded'
      )
    },
  },
)

const complaintSlice = createSlice({
  name: 'complaint',
  initialState,
  reducers: {
    updateDraftField: (
      state,
      action: { payload: { field: keyof ComplaintDraft; value: string } },
    ) => {
      const { field, value } = action.payload
      ;(state.draft[field] as string) = value
      if (state.completenessAssessment) recalculateCompleteness(state)
      if (relevantEnhancementFields.has(field))
        state.enhancementResultsStale = true
      state.requestStatus = 'idle'
      state.error = null
    },
    resetComplaintDraft: () => initialState,
    updateCopilotInput: (state, action: { payload: string }) => {
      state.copilotInput = action.payload
      state.processingError = null
    },
    updateCorrectionInstruction: (state, action: { payload: string }) => {
      state.correctionInstruction = action.payload
      state.correctionError = null
    },
    selectDocument: (state, action: { payload: SelectedDocument }) => {
      state.selectedDocument = action.payload
      state.documentStatus = 'selected'
      state.documentError = null
      state.documentWarnings = []
    },
    removeDocument: (state) => {
      state.selectedDocument = null
      state.documentStatus = 'idle'
      state.documentError = null
      state.documentWarnings = []
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(commitComplaintDraft.pending, (state) => {
        state.requestStatus = 'saving'
        state.error = null
      })
      .addCase(commitComplaintDraft.fulfilled, (state, action) => {
        state.requestStatus = 'succeeded'
        state.savedRecord = action.payload
      })
      .addCase(commitComplaintDraft.rejected, (state, action) => {
        if (action.meta.condition) return
        state.requestStatus = 'failed'
        state.error = String(
          action.payload ??
            action.error.message ??
            'Unable to commit complaint',
        )
      })
      .addCase(processTextComplaint.pending, (state) => {
        beginNewIntake(state)
        state.processingStatus = 'processing'
        state.processingError = null
        state.warnings = []
      })
      .addCase(processTextComplaint.fulfilled, (state, action) => {
        state.sourceType = 'TEXT'
        state.processingStatus = 'succeeded'
        state.lastProcessedInputLength = action.payload.input_length
        state.warnings = action.payload.warnings
        state.conversation.push(
          {
            id: `${Date.now()}-user`,
            role: 'user',
            content: state.copilotInput,
          },
          {
            id: `${Date.now()}-assistant`,
            role: 'assistant',
            content: action.payload.assistant_message,
          },
        )
        for (const [source, target] of Object.entries(extractionMap) as Array<
          [keyof ExtractedComplaint, keyof ComplaintDraft]
        >) {
          const value = action.payload.extracted_complaint[source]
          if (value !== null) (state.draft[target] as string) = value
        }
        applyAssessment(state, action.payload.quality_assessment)
        applyEnhancements(state, action.payload)
      })
      .addCase(processTextComplaint.rejected, (state, action) => {
        if (action.meta.condition) return
        state.processingStatus = 'failed'
        state.processingError = String(
          action.payload ??
            action.error.message ??
            'Unable to process complaint text',
        )
      })
      .addCase(processDocumentComplaint.pending, (state) => {
        beginNewIntake(state)
        state.documentStatus = 'uploading'
        state.documentError = null
        state.documentWarnings = []
      })
      .addCase(processDocumentComplaint.fulfilled, (state, action) => {
        state.sourceType = 'PDF'
        state.documentStatus = 'succeeded'
        state.documentWarnings = action.payload.warnings
        state.conversation.push(
          {
            id: `${Date.now()}-pdf-user`,
            role: 'user',
            content: `Uploaded PDF: ${action.payload.document.filename}`,
          },
          {
            id: `${Date.now()}-pdf-assistant`,
            role: 'assistant',
            content: action.payload.assistant_message,
          },
        )
        for (const [source, target] of Object.entries(extractionMap) as Array<
          [keyof ExtractedComplaint, keyof ComplaintDraft]
        >) {
          const value = action.payload.extracted_complaint[source]
          if (value !== null) (state.draft[target] as string) = value
        }
        applyAssessment(state, action.payload.quality_assessment)
        applyEnhancements(state, action.payload)
      })
      .addCase(processDocumentComplaint.rejected, (state, action) => {
        if (action.meta.condition) return
        state.documentStatus = 'failed'
        state.documentError = String(
          action.payload ??
            action.error.message ??
            'Unable to process PDF complaint',
        )
      })
      .addCase(applyCorrection.pending, (state) => {
        state.correctionStatus = 'processing'
        state.correctionError = null
      })
      .addCase(applyCorrection.fulfilled, (state, action) => {
        const response = action.payload
        state.correctionStatus =
          response.status === 'CLARIFICATION_REQUIRED'
            ? 'clarification_required'
            : 'succeeded'
        state.changedFields = response.changed_fields
        state.clarificationQuestion = response.patch.clarification_question
        state.warnings = response.warnings
        state.conversation.push(
          {
            id: `${Date.now()}-correction-user`,
            role: 'user',
            content: state.correctionInstruction,
          },
          {
            id: `${Date.now()}-correction-assistant`,
            role: 'assistant',
            content: response.assistant_message,
          },
        )
        for (const [source, target] of Object.entries(extractionMap) as Array<
          [keyof ExtractedComplaint, keyof ComplaintDraft]
        >) {
          ;(state.draft[target] as string) =
            response.updated_complaint[source] ?? ''
        }
        state.draft.complaintCategory =
          response.updated_complaint.complaint_category ?? ''
        applyAssessment(state, response.quality_assessment)
        applyEnhancements(state, response)
        state.correctionInstruction = ''
      })
      .addCase(applyCorrection.rejected, (state, action) => {
        if (action.meta.condition) return
        state.correctionStatus = 'failed'
        state.correctionError = String(
          action.payload ??
            action.error.message ??
            'Unable to apply correction',
        )
      })
  },
})

export const {
  removeDocument,
  resetComplaintDraft,
  selectDocument,
  updateCopilotInput,
  updateCorrectionInstruction,
  updateDraftField,
} = complaintSlice.actions
export const complaintReducer = complaintSlice.reducer
