import { createAsyncThunk, createSlice } from '@reduxjs/toolkit'

import {
  commitComplaint,
  processComplaintDocument,
  processComplaintText,
} from './api'
import type {
  ComplaintDraft,
  ComplaintRecord,
  ConversationMessage,
  ExtractedComplaint,
  SelectedDocument,
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
      state.requestStatus = 'idle'
      state.error = null
    },
    resetComplaintDraft: () => initialState,
    updateCopilotInput: (state, action: { payload: string }) => {
      state.copilotInput = action.payload
      state.processingError = null
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
  },
})

export const {
  removeDocument,
  resetComplaintDraft,
  selectDocument,
  updateCopilotInput,
  updateDraftField,
} = complaintSlice.actions
export const complaintReducer = complaintSlice.reducer
