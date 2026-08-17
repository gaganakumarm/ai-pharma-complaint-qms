import { zodResolver } from '@hookform/resolvers/zod'
import type { ChangeEvent, ReactNode } from 'react'
import { useForm } from 'react-hook-form'

import { useAppDispatch, useAppSelector } from '../../app/hooks'
import {
  commitComplaintDraft,
  resetComplaintDraft,
  updateDraftField,
} from './complaintSlice'
import { complaintFormSchema, type ComplaintFormValues } from './schema'
import type { ComplaintDraft } from './types'

const inputClass =
  'mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm outline-none focus:border-teal-500 focus:ring-2 focus:ring-teal-100'

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <fieldset className="border-t border-slate-200 pt-5">
      <legend className="pr-3 font-semibold text-slate-900">{title}</legend>
      <div className="mt-3 grid gap-4 md:grid-cols-2">{children}</div>
    </fieldset>
  )
}

export function ComplaintWorkspace() {
  const dispatch = useAppDispatch()
  const complaint = useAppSelector((state) => state.complaint)
  const { draft, requestStatus, savedRecord, error } = complaint
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isValid },
  } = useForm<ComplaintFormValues>({
    resolver: zodResolver(complaintFormSchema),
    mode: 'onChange',
    values: draft,
  })

  const bind = (field: keyof ComplaintDraft) => {
    const registration = register(field)
    return {
      ...registration,
      onChange: (
        event: ChangeEvent<
          HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement
        >,
      ) => {
        void registration.onChange(event)
        dispatch(updateDraftField({ field, value: event.target.value }))
      },
      'aria-invalid': Boolean(errors[field]),
      'aria-describedby': errors[field] ? `${field}-error` : undefined,
    }
  }
  const validation = (field: keyof ComplaintFormValues) =>
    errors[field] ? (
      <p
        id={`${field}-error`}
        role="alert"
        className="mt-1 text-xs text-red-600"
      >
        {errors[field]?.message}
      </p>
    ) : null
  const status =
    requestStatus === 'saving'
      ? 'Saving'
      : requestStatus === 'succeeded'
        ? 'Committed'
        : requestStatus === 'failed'
          ? 'Error'
          : isValid
            ? 'Ready to Commit'
            : 'Pending Triage'
  const onSubmit = () => {
    if (requestStatus !== 'saving' && requestStatus !== 'succeeded')
      void dispatch(commitComplaintDraft(draft))
  }
  const resetForm = () => {
    dispatch(resetComplaintDraft())
    reset()
  }

  return (
    <main className="mx-auto grid max-w-7xl gap-6 px-6 py-8 xl:grid-cols-[minmax(0,2fr)_minmax(300px,1fr)]">
      <form
        aria-label="Log Customer Complaint"
        onSubmit={handleSubmit(onSubmit)}
        className="space-y-7 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"
      >
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 className="text-xl font-semibold">Log Customer Complaint</h2>
            <p className="mt-1 text-sm text-slate-500">
              Required fields are marked with an asterisk.
            </p>
          </div>
          <span
            role="status"
            className="rounded-full bg-teal-50 px-3 py-1 text-xs font-semibold text-teal-700"
          >
            {status}
          </span>
        </div>
        <Section title="Origin and Customer Details">
          <label className="text-sm font-medium">
            Complaint Source
            <input className={inputClass} {...bind('complaintSource')} />
          </label>
          <label className="text-sm font-medium">
            Customer Name *
            <input className={inputClass} {...bind('customerName')} />
            {validation('customerName')}
          </label>
        </Section>
        <Section title="Product and Batch Identification">
          <label className="text-sm font-medium">
            Product Type
            <select className={inputClass} {...bind('productType')}>
              <option value="UNKNOWN">Unknown</option>
              <option value="API">API</option>
              <option value="FDF">FDF</option>
            </select>
          </label>
          <label className="text-sm font-medium">
            Product Name *
            <input className={inputClass} {...bind('productName')} />
            {validation('productName')}
          </label>
          <label className="text-sm font-medium">
            Product Strength/Grade
            <input className={inputClass} {...bind('productStrengthGrade')} />
          </label>
          <label className="text-sm font-medium">
            Batch/Lot Number *
            <input className={inputClass} {...bind('batchLotNumber')} />
            {validation('batchLotNumber')}
          </label>
          <label className="text-sm font-medium">
            Affected Quantity
            <input className={inputClass} {...bind('affectedQuantity')} />
          </label>
          <label className="text-sm font-medium">
            Manufacturing Date
            <input
              placeholder="e.g. March 2026"
              className={inputClass}
              {...bind('manufacturingDate')}
            />
          </label>
          <label className="text-sm font-medium">
            Expiry/Retest Date
            <input
              placeholder="e.g. Not Provided"
              className={inputClass}
              {...bind('expiryRetestDate')}
            />
          </label>
        </Section>
        <Section title="Facility and Material Impact">
          <label className="text-sm font-medium">
            Originating Site/Block
            <input className={inputClass} {...bind('originatingSiteBlock')} />
          </label>
          <label className="text-sm font-medium">
            Impacted Non-Product Materials
            <textarea
              className={inputClass}
              {...bind('impactedNonProductMaterials')}
            />
          </label>
        </Section>
        <Section title="Defect Analysis">
          <label className="text-sm font-medium">
            Complaint Category *
            <input className={inputClass} {...bind('complaintCategory')} />
            {validation('complaintCategory')}
          </label>
          <label className="text-sm font-medium md:col-span-2">
            Complaint Description *
            <textarea
              rows={4}
              className={inputClass}
              {...bind('complaintDescription')}
            />
            {validation('complaintDescription')}
          </label>
        </Section>
        <Section title="AI Copilot Risk Assessment">
          <p className="rounded-lg bg-amber-50 p-3 text-sm text-amber-800 md:col-span-2">
            AI assessment is unavailable in Sprint 1. These optional fields may
            be entered manually.
          </p>
          <label className="text-sm font-medium">
            Suggested Severity
            <select className={inputClass} {...bind('suggestedSeverity')}>
              <option value="">Not assessed</option>
              <option value="MINOR">Minor</option>
              <option value="MAJOR">Major</option>
              <option value="CRITICAL">Critical</option>
            </select>
          </label>
          <label className="text-sm font-medium md:col-span-2">
            Initial Risk Assessment
            <textarea
              className={inputClass}
              {...bind('initialRiskAssessment')}
            />
          </label>
          <label className="text-sm font-medium md:col-span-2">
            Suggested Next Action
            <textarea className={inputClass} {...bind('suggestedNextAction')} />
          </label>
        </Section>
        {error && (
          <p
            role="alert"
            className="rounded-lg bg-red-50 p-3 text-sm text-red-700"
          >
            {error}. Your form values have been preserved.
          </p>
        )}
        <div className="flex flex-wrap justify-end gap-3">
          <button
            type="button"
            onClick={resetForm}
            className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-semibold"
          >
            Reset Form
          </button>
          <button
            type="submit"
            disabled={
              !isValid ||
              requestStatus === 'saving' ||
              requestStatus === 'succeeded'
            }
            className="rounded-lg bg-teal-600 px-4 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-50"
          >
            {requestStatus === 'saving' ? 'Saving…' : 'Commit to QMS Ledger'}
          </button>
        </div>
      </form>
      <aside className="space-y-5 rounded-2xl border border-slate-200 bg-slate-900 p-6 text-white shadow-sm">
        <div>
          <p className="text-xs font-semibold uppercase tracking-widest text-teal-300">
            AIVOA Copilot
          </p>
          <h2 className="mt-2 text-xl font-semibold">Review summary</h2>
        </div>
        {savedRecord ? (
          <div className="rounded-xl bg-white/10 p-4">
            <p className="text-xs text-slate-300">Complaint number</p>
            <p className="mt-1 text-lg font-bold text-teal-300">
              {savedRecord.complaint_number}
            </p>
            <p className="mt-3 text-sm font-semibold">{savedRecord.status}</p>
            <dl className="mt-4 space-y-2 text-sm">
              <div>
                <dt className="text-slate-400">Product</dt>
                <dd>{savedRecord.product_name}</dd>
              </div>
              <div>
                <dt className="text-slate-400">Batch</dt>
                <dd>{savedRecord.batch_lot_number}</dd>
              </div>
            </dl>
          </div>
        ) : (
          <p className="rounded-xl border border-dashed border-slate-600 p-5 text-sm leading-6 text-slate-300">
            Complete the five required fields to make the complaint ready for
            commitment. AI processing is not active.
          </p>
        )}
      </aside>
    </main>
  )
}
