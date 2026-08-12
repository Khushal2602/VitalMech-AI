import { AlertTriangle, TrendingUp, Info, BookOpen } from 'lucide-react'

const SEVERITY_PILL = {
  low:    'bg-green-900/60 text-green-300 border-green-700',
  medium: 'bg-yellow-900/60 text-yellow-300 border-yellow-700',
  high:   'bg-red-900/60 text-red-300 border-red-700',
}

function ConfidenceBar({ confidence }) {
  const pct   = Math.round((confidence ?? 0) * 100)
  const color = pct >= 75 ? 'bg-red-500' : pct >= 50 ? 'bg-yellow-500' : 'bg-blue-500'
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 rounded-full bg-gray-700 overflow-hidden">
        <div
          className={`h-1.5 rounded-full transition-all duration-700 ${color}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xs text-gray-400 tabular-nums w-8 text-right">{pct}%</span>
    </div>
  )
}

function EmptyState({ isLoading }) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-gray-700">
      <TrendingUp className="w-8 h-8 mb-2 opacity-40" />
      <p className="text-sm">{isLoading ? 'Analysing fault patterns…' : 'Run a diagnosis to see results'}</p>
    </div>
  )
}

export default function FaultCard({ result, isLoading }) {
  const symptoms = result?.diagnosis?.symptoms ?? []
  const faults   = result?.diagnosis?.faults ?? []
  const rc       = result?.diagnosis?.root_cause
  const evidence = result?.retrieved_knowledge ?? []

  return (
    <div className="bg-gray-800/80 rounded-xl border border-gray-700">

      {/* Card header */}
      <div className="flex items-center gap-2 px-5 pt-5 pb-4 border-b border-gray-700/50">
        <AlertTriangle className="w-4 h-4 text-gray-400" />
        <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
          Fault Analysis
        </h2>
      </div>

      {!result ? (
        <EmptyState isLoading={isLoading} />
      ) : (
        <div className="p-5 space-y-6">

          {/* ── Detected Symptoms ── */}
          {symptoms.length > 0 && (
            <section>
              <h3 className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2.5">
                Detected Symptoms
              </h3>
              <div className="flex flex-wrap gap-2">
                {symptoms.map((s, i) => (
                  <span
                    key={i}
                    title={s.description}
                    className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full
                                text-xs font-medium border cursor-default select-none
                                ${SEVERITY_PILL[s.severity] ?? SEVERITY_PILL.low}`}
                  >
                    <AlertTriangle className="w-3 h-3 flex-shrink-0" />
                    {s.name}
                    <span className="opacity-60 capitalize">({s.severity})</span>
                  </span>
                ))}
              </div>
            </section>
          )}

          {/* ── Probable Faults ── */}
          {faults.length > 0 && (
            <section>
              <h3 className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-3">
                Probable Faults
              </h3>
              <div className="space-y-3.5">
                {faults.map((fault, i) => (
                  <div key={i} className={`rounded-lg p-3 border transition-colors
                    ${i === 0
                      ? 'bg-gray-700/60 border-gray-600'
                      : 'bg-gray-800/40 border-gray-700/50'}`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        {i === 0 && (
                          <span className="text-xs bg-blue-900/80 text-blue-300 border border-blue-700
                                           px-1.5 py-0.5 rounded font-semibold">
                            TOP
                          </span>
                        )}
                        <span className={`text-sm font-semibold ${i === 0 ? 'text-gray-100' : 'text-gray-300'}`}>
                          {fault.name}
                        </span>
                      </div>
                    </div>
                    <ConfidenceBar confidence={fault.confidence} />
                    {fault.description && (
                      <p className="text-xs text-gray-500 mt-2 leading-relaxed">{fault.description}</p>
                    )}
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* ── Root Cause ── */}
          {rc && (
            <section>
              <h3 className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2.5 flex items-center gap-1.5">
                <Info className="w-3.5 h-3.5" />
                Root Cause Analysis
              </h3>
              <div className="bg-gray-700/30 rounded-lg p-3.5 border border-gray-700/50">
                <p className="text-sm text-gray-200 leading-relaxed mb-3">{rc.summary}</p>
                {rc.cause_chain?.length > 0 && (
                  <ol className="space-y-1.5">
                    {rc.cause_chain.map((cause, i) => (
                      <li key={i} className="flex items-start gap-2.5 text-xs text-gray-400">
                        <span className="flex-shrink-0 w-5 h-5 rounded-full bg-blue-900/60 text-blue-400
                                         text-xs font-bold flex items-center justify-center mt-0.5">
                          {i + 1}
                        </span>
                        <span className="leading-relaxed">{cause}</span>
                      </li>
                    ))}
                  </ol>
                )}
              </div>
            </section>
          )}

          {/* ── Retrieved Evidence ── */}
          {evidence.length > 0 && (
            <section>
              <h3 className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2.5 flex items-center gap-1.5">
                <BookOpen className="w-3.5 h-3.5" />
                Retrieved Knowledge Evidence
              </h3>
              <div className="flex flex-wrap gap-2">
                {evidence.map((doc, i) => (
                  <span
                    key={i}
                    className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md
                               bg-gray-700/60 border border-gray-600/50 text-xs text-gray-400"
                  >
                    <BookOpen className="w-3 h-3 text-gray-500 flex-shrink-0" />
                    {doc}
                  </span>
                ))}
              </div>
            </section>
          )}

        </div>
      )}
    </div>
  )
}
