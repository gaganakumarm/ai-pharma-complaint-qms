function PlaceholderCard({ title, body }: { title: string; body: string }) {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="mb-5 h-1 w-12 rounded-full bg-teal-500" />
      <h2 className="text-xl font-semibold text-slate-900">{title}</h2>
      <p className="mt-2 text-sm leading-6 text-slate-500">{body}</p>
      <div className="mt-8 rounded-xl border border-dashed border-slate-300 bg-slate-50 px-4 py-12 text-center text-sm text-slate-400">
        Sprint 1 workspace
      </div>
    </section>
  )
}

export function ComplaintWorkspace() {
  return (
    <main className="mx-auto grid max-w-7xl gap-6 px-6 py-10 lg:grid-cols-2">
      <PlaceholderCard
        title="Log Customer Complaint"
        body="Capture and validate pharmaceutical product quality concerns."
      />
      <PlaceholderCard
        title="AIVOA Copilot"
        body="Assisted complaint review will become available in a future sprint."
      />
    </main>
  )
}
