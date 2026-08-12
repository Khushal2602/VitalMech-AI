import { CheckCircle, Circle, Loader, Stethoscope, Search, GitBranch, Wrench } from 'lucide-react'

const AGENTS = [
  {
    step: 1,
    label: 'Symptom Detection',
    description: 'Classifying sensor anomalies and severity levels',
    Icon: Stethoscope,
    resultKey: 'symptoms',
    resultLabel: (r) => r?.diagnosis?.symptoms?.length
      ? `${r.diagnosis.symptoms.length} symptom${r.diagnosis.symptoms.length > 1 ? 's' : ''} detected`
      : null,
  },
  {
    step: 2,
    label: 'Fault Analysis',
    description: 'Identifying probable mechanical faults via RAG',
    Icon: Search,
    resultKey: 'faults',
    resultLabel: (r) => r?.diagnosis?.faults?.[0]
      ? `Top: ${r.diagnosis.faults[0].name}`
      : null,
  },
  {
    step: 3,
    label: 'Root Cause Analysis',
    description: 'Mapping cause-effect chain',
    Icon: GitBranch,
    resultKey: 'root_cause',
    resultLabel: (r) => r?.diagnosis?.root_cause?.cause_chain?.length
      ? `${r.diagnosis.root_cause.cause_chain.length} causes identified`
      : null,
  },
  {
    step: 4,
    label: 'Repair Guidance',
    description: 'Generating prioritised maintenance steps',
    Icon: Wrench,
    resultKey: 'repair_guidance',
    resultLabel: (r) => r?.diagnosis?.repair_guidance?.steps?.length
      ? `${r.diagnosis.repair_guidance.steps.length} steps · ${r.diagnosis.repair_guidance.urgency}`
      : null,
  },
]

export default function AgentTimeline({ agentStep, isLoading, result }) {
  const isDone = agentStep === 5

  return (
    <div>
      <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
        Diagnostic Pipeline
      </h2>

      <div className="bg-gray-800/80 rounded-xl border border-gray-700 overflow-hidden">
        <ol className="divide-y divide-gray-700/50">
          {AGENTS.map(({ step, label, description, Icon, resultLabel }) => {
            const isComplete = isDone || agentStep > step
            const isActive   = agentStep === step && isLoading
            const summary    = result ? resultLabel(result) : null

            return (
              <li
                key={step}
                className={`flex items-start gap-3 px-4 py-3 transition-colors duration-300
                  ${isComplete ? 'bg-green-950/10' : isActive ? 'bg-blue-950/20' : ''}`}
              >
                {/* Step icon */}
                <div className="mt-0.5 flex-shrink-0 w-5 h-5 flex items-center justify-center">
                  {isComplete ? (
                    <CheckCircle className="w-5 h-5 text-green-400" />
                  ) : isActive ? (
                    <Loader className="w-5 h-5 text-blue-400 animate-spin" />
                  ) : (
                    <Circle className="w-5 h-5 text-gray-700" />
                  )}
                </div>

                {/* Agent icon */}
                <div className={`mt-0.5 flex-shrink-0 ${
                  isComplete ? 'text-green-500' : isActive ? 'text-blue-400' : 'text-gray-700'
                }`}>
                  <Icon className="w-4 h-4" />
                </div>

                {/* Text */}
                <div className="flex-1 min-w-0">
                  <p className={`text-sm font-medium leading-tight ${
                    isComplete ? 'text-gray-200' : isActive ? 'text-blue-300' : 'text-gray-600'
                  }`}>
                    Agent {step}: {label}
                  </p>
                  {summary && isComplete ? (
                    <p className="text-xs text-green-400/80 mt-0.5 truncate">{summary}</p>
                  ) : (
                    <p className="text-xs text-gray-700 mt-0.5">{description}</p>
                  )}
                </div>
              </li>
            )
          })}
        </ol>
      </div>
    </div>
  )
}
