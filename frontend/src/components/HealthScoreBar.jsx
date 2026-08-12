import { ShieldCheck, ShieldAlert, ShieldX, Cpu, Database } from 'lucide-react'

const SEVERITY_MAP = {
  low:      { label: 'Low Risk',       color: 'text-green-400',  bar: 'bg-green-500',  border: 'border-green-800',  bg: 'bg-green-950/40',  Icon: ShieldCheck },
  medium:   { label: 'Medium Risk',    color: 'text-yellow-400', bar: 'bg-yellow-500', border: 'border-yellow-800', bg: 'bg-yellow-950/40', Icon: ShieldAlert },
  high:     { label: 'High Risk',      color: 'text-orange-400', bar: 'bg-orange-500', border: 'border-orange-800', bg: 'bg-orange-950/40', Icon: ShieldAlert },
  critical: { label: 'Critical',       color: 'text-red-400',    bar: 'bg-red-500',    border: 'border-red-800',    bg: 'bg-red-950/40',    Icon: ShieldX    },
  unknown:  { label: 'Unknown',        color: 'text-gray-400',   bar: 'bg-gray-600',   border: 'border-gray-700',   bg: 'bg-gray-800',      Icon: ShieldCheck },
}

export default function HealthScoreBar({ result }) {
  if (!result) return null

  const sev   = SEVERITY_MAP[result.severity] ?? SEVERITY_MAP.unknown
  const { Icon } = sev

  // Health score: invert confidence (high confidence in a fault = low health)
  const healthPct = Math.max(0, Math.round(100 - (result.overall_confidence ?? 0) * 100))

  return (
    <div className={`rounded-xl border ${sev.border} ${sev.bg} px-5 py-4`}>
      <div className="flex flex-wrap items-center gap-x-6 gap-y-3">

        {/* Severity badge */}
        <div className="flex items-center gap-2 min-w-fit">
          <Icon className={`w-5 h-5 ${sev.color}`} />
          <div>
            <p className="text-xs text-gray-500 leading-none">Overall Severity</p>
            <p className={`text-lg font-bold leading-tight ${sev.color}`}>{sev.label}</p>
          </div>
        </div>

        {/* Health score gauge */}
        <div className="flex-1 min-w-40">
          <div className="flex justify-between text-xs mb-1">
            <span className="text-gray-500">Machine Health Score</span>
            <span className={`font-semibold tabular-nums ${sev.color}`}>{healthPct}%</span>
          </div>
          <div className="h-2 rounded-full bg-gray-700 overflow-hidden">
            <div
              className={`h-2 rounded-full transition-all duration-700 ${sev.bar}`}
              style={{ width: `${healthPct}%` }}
            />
          </div>
        </div>

        {/* Source badges */}
        <div className="flex flex-col gap-1.5 min-w-fit">
          <div className="flex items-center gap-1.5 text-xs">
            <Cpu className="w-3.5 h-3.5 text-gray-500" />
            <span className="text-gray-500">AI:</span>
            <span className={`font-medium ${result.ai_source === 'granite' ? 'text-blue-400' : 'text-gray-300'}`}>
              {result.ai_source === 'granite' ? 'IBM Granite' : 'Rule-Based Engine'}
            </span>
          </div>
          <div className="flex items-center gap-1.5 text-xs">
            <Database className="w-3.5 h-3.5 text-gray-500" />
            <span className="text-gray-500">RAG:</span>
            <span className="text-gray-300 font-medium capitalize">{result.rag_backend}</span>
          </div>
        </div>

      </div>
    </div>
  )
}
