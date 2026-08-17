import { createAsyncThunk, createSlice } from '@reduxjs/toolkit'

import { commitComplaint } from './api'
import type { ComplaintDraft, ComplaintRecord } from './types'

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
  requestStatus: 'idle' | 'saving' | 'succeeded' | 'failed'
  savedRecord: ComplaintRecord | null
  error: string | null
}

const initialState: ComplaintState = {
  draft: initialDraft,
  requestStatus: 'idle',
  savedRecord: null,
  error: null,
}

export const commitComplaintDraft = createAsyncThunk(
  'complaint/commit',
  async (draft: ComplaintDraft, { rejectWithValue }) => {
    try {
      return await commitComplaint(draft)
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
  },
})

export const { resetComplaintDraft, updateDraftField } = complaintSlice.actions
export const complaintReducer = complaintSlice.reducer
