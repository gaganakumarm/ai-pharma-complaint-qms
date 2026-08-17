import type {
  CompletenessAssessment,
  DuplicateMatch,
  RcaCapaRecommendations,
} from './types'

const label = (field: string) =>
  field
    .replaceAll('_', ' ')
    .replace(/\b\w/g, (character) => character.toUpperCase())

export function EnhancementPanels({
  completeness,
  duplicates,
  rcaCapa,
  stale,
}: {
  completeness: CompletenessAssessment | null
  duplicates: DuplicateMatch[]
  rcaCapa: RcaCapaRecommendations | null
  stale: boolean
}) {
  if (!completeness && !rcaCapa) return null
  return (
    <section aria-label="Sprint 6 decision support" className="space-y-4">
      {completeness && (
        <article className="rounded-xl border border-slate-200 p-4">
          <h3 className="font-semibold">Complaint completeness</h3>
          <p className="mt-2 font-medium">
            {completeness.status.replace('_', ' ')} —{' '}
            {completeness.completeness_percentage}%
          </p>
          <p className="text-sm text-slate-600">
            {completeness.required_fields_present} of{' '}
            {completeness.total_required_fields} required fields present
          </p>
          {completeness.missing_required_fields.length > 0 && (
            <p className="mt-2 text-sm">
              Missing required:{' '}
              {completeness.missing_required_fields.map(label).join(', ')}
            </p>
          )}
          {completeness.missing_recommended_fields.length > 0 && (
            <p className="mt-1 text-sm">
              Missing recommended:{' '}
              {completeness.missing_recommended_fields.map(label).join(', ')}
            </p>
          )}
          <p className="mt-2 text-sm text-slate-600">{completeness.guidance}</p>
        </article>
      )}
      <article className="rounded-xl border border-slate-200 p-4">
        <h3 className="font-semibold">Possible duplicate complaints</h3>
        {stale && (
          <p role="status" className="mt-2 text-sm font-medium text-amber-800">
            Results may be outdated after relevant manual edits.
          </p>
        )}
        {duplicates.length === 0 ? (
          <p className="mt-2 text-sm">No possible matches found</p>
        ) : (
          <ol className="mt-3 space-y-3">
            {duplicates.map((match) => (
              <li
                key={match.complaint_id}
                className="rounded-lg bg-slate-50 p-3 text-sm"
              >
                <p className="font-semibold">
                  {match.complaint_number} — {match.similarity_score}%
                </p>
                <p>
                  {match.product_name} / {match.batch_lot_number}
                </p>
                <p>{match.complaint_category}</p>
                <p>{match.match_level.replace('_', ' ')}</p>
                <ul className="list-disc pl-5">
                  {match.match_reasons.map((reason) => (
                    <li key={reason}>{reason}</li>
                  ))}
                </ul>
              </li>
            ))}
          </ol>
        )}
        <p className="mt-3 text-sm font-medium">
          Possible match only — QA review required
        </p>
      </article>
      {rcaCapa && (
        <article className="rounded-xl border border-slate-200 p-4">
          <h3 className="font-semibold">
            Investigation and CAPA recommendations
          </h3>
          {stale && (
            <p className="mt-2 text-sm text-amber-800">
              Results may be outdated.
            </p>
          )}
          <h4 className="mt-3 font-medium">Potential root-cause hypotheses</h4>
          <ul className="list-disc space-y-2 pl-5 text-sm">
            {rcaCapa.potential_root_causes.map((cause) => (
              <li key={cause.statement}>
                <strong>{cause.statement}</strong>: {cause.rationale}. Evidence
                required: {cause.evidence_required}
              </li>
            ))}
          </ul>
          <h4 className="mt-3 font-medium">Investigation areas</h4>
          <ul className="list-disc pl-5 text-sm">
            {rcaCapa.investigation_areas.map((area) => (
              <li key={area}>{area}</li>
            ))}
          </ul>
          <h4 className="mt-3 font-medium">
            Corrective-action recommendations
          </h4>
          <ul className="list-disc pl-5 text-sm">
            {rcaCapa.corrective_actions.map((item) => (
              <li key={item.action}>
                {item.action} — {item.purpose}; verification:{' '}
                {item.verification}
              </li>
            ))}
          </ul>
          <h4 className="mt-3 font-medium">
            Preventive-action recommendations
          </h4>
          <ul className="list-disc pl-5 text-sm">
            {rcaCapa.preventive_actions.map((item) => (
              <li key={item.action}>
                {item.action} — {item.purpose}; effectiveness check:{' '}
                {item.effectiveness_check}
              </li>
            ))}
          </ul>
          <h4 className="mt-3 font-medium">Assumptions and limitations</h4>
          <ul className="list-disc pl-5 text-sm">
            {rcaCapa.assumptions_or_limitations.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
          <p className="mt-3 rounded-lg bg-amber-50 p-3 text-sm font-medium">
            {rcaCapa.disclaimer}
          </p>
          <p className="mt-2 text-sm font-semibold">
            Human review required. These are not approved CAPA.
          </p>
        </article>
      )}
    </section>
  )
}
