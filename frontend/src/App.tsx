import { ComplaintWorkspace } from './features/complaints/ComplaintWorkspace'

export function App() {
  return (
    <div className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto max-w-7xl px-6 py-5">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-teal-600">
            Quality Management System
          </p>
          <h1 className="mt-1 text-2xl font-bold text-slate-950">
            Pharmaceutical Customer Complaints
          </h1>
        </div>
      </header>
      <ComplaintWorkspace />
    </div>
  )
}
