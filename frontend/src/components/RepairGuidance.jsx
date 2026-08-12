import { Wrench, AlertCircle, Clock, CheckCircle } from 'lucide-react'

const URGENCY_CONFIG = {
  immediate: {
    label: 'Immediate Action Required',
    sublabel: 'Stop machine — risk of catastrophic failure',
    textColor: 'text-red-300',
    border: 'border-red-700',
    bg: 'bg-red-950/40',
    barColor: 'bg-red-500',
    numBg: 'bg-red-900/60 text-red-300',
    Icon: AlertCircle,
  },
  soon: {
    label: 'Action Required Soon',
    sublabel: 'Schedule repair within 24–72 hours',
    textColor: 'text-yellow-300',
    border: 'border-yellow-700',
    bg: 'bg-yellow-950/30',
    barColor: 'bg-yellow-500',
    numBg: 'bg-yellow-900/60 text-yellow-300',
    Icon: Clock,
  },
  scheduled: {
    label: 'Schedule for Maintenance',
    sublabel: 'Plan repair at next maintenance window',
    textColor: 'text-green-300',
    border: 'border-green-700',
    bg: 'bg-green-950/20',
    barColor: 'bg-green-500',
    numBg: 'bg-green-900/60 text-green-300',
    Icon: CheckCircle,
  },
}

function EmptyState({ isLoading }) {
  return (
    <div className="flex flex-col items-center justify-center py-10 text-gray-700">
      <Wrench className="w-7 h-7 mb-2 opacity-40" />
      <p className="text-sm">{isLoading ? 'Generating repair guidance…' : 'Repair guidance will appear after diagnosis'}</p>
    </div>
  )
}

export default function RepairGuidance({ result, isLoading }) {
  const guidance   = result?.diagnosis?.repair_guidance
  const urgencyKey = guidance?.urgency || 'scheduled'
  const cfg        = URGENCY_CONFIG[urgencyKey] ?? URGENCY_CONFIG.scheduled
  const { Icon }   = cfg
  const steps      = guidance?.steps ?? []

  return (
    <div className="bg-gray-800/80 rounded-xl border border-gray-700 overflow-hidden">

      {/* Card header */}
      <div className="flex items-center gap-2 px-5 pt-5 pb-4 border-b border-gray-700/50">
        <Wrench className="w-4 h-4 text-gray-400" />
        <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
          Repair Guidance
        </h2>
      </div>

      {!result ? (
        <EmptyState isLoading={isLoading} />
      ) : guidance ? (
        <div className="p-5">

          {/* Urgency hero */}
          <div className={`flex items-start gap-3 rounded-xl border p-4 mb-5 ${cfg.border} ${cfg.bg}`}>
            <Icon className={`w-5 h-5 mt-0.5 flex-shrink-0 ${cfg.textColor}`} />
            <div>
              <p className={`text-sm font-bold ${cfg.textColor}`}>{cfg.label}</p>
              <p className="text-xs text-gray-500 mt-0.5">{cfg.sublabel}</p>
            </div>
          </div>

          {/* Steps */}
          {steps.length > 0 && (
            <ol className="space-y-2.5">
              {steps.map((step, i) => (
                <li key={i} className="flex items-start gap-3 group">
                  <span className={`flex-shrink-0 w-6 h-6 rounded-full text-xs font-bold
                                    flex items-center justify-center mt-0.5 ${cfg.numBg}`}>
                    {i + 1}
                  </span>
                  <p className="text-sm text-gray-300 leading-relaxed pt-0.5">
                    {step.replace(/^\d+\.\s*/, '')}
                  </p>
                </li>
              ))}
            </ol>
          )}

        </div>
      ) : (
        <div className="px-5 pb-5 pt-3 text-sm text-gray-500">No repair guidance available for this diagnosis.</div>
      )}
    </div>
  )
}
