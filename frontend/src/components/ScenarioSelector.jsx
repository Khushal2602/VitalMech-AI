import { Cpu, ChevronRight } from 'lucide-react'

const FAULT_ICONS = {
  'normal_operation': '✦',
  'bearing_failure':  '⚙',
  'overheating':      '🌡',
  'cavitation':       '≋',
  'shaft_misalignment': '↔',
  'oil_starvation':   '⬡',
  'imbalance':        '◎',
  'electrical_fault': '⚡',
}

const FAULT_ACCENT = {
  'normal_operation': 'border-green-700 hover:border-green-500',
  'bearing_failure':  'border-orange-700 hover:border-orange-500',
  'overheating':      'border-red-700 hover:border-red-500',
  'cavitation':       'border-cyan-700 hover:border-cyan-500',
  'shaft_misalignment': 'border-yellow-700 hover:border-yellow-500',
  'oil_starvation':   'border-amber-700 hover:border-amber-500',
  'imbalance':        'border-purple-700 hover:border-purple-500',
  'electrical_fault': 'border-blue-700 hover:border-blue-500',
}

export default function ScenarioSelector({ scenarios, selected, onChange }) {
  const active = scenarios.find((s) => s.id === selected)

  return (
    <div>
      <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
        Machine Scenario
      </label>

      {/* Horizontal scrollable card strip */}
      <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-hide">
        {scenarios.map((s) => {
          const isSelected = s.id === selected
          const accent = FAULT_ACCENT[s.id] ?? 'border-gray-700 hover:border-gray-500'
          return (
            <button
              key={s.id}
              onClick={() => onChange(s.id)}
              className={`flex-shrink-0 rounded-xl border px-3 py-2.5 text-left
                          transition-all duration-150 min-w-[130px]
                          ${isSelected
                            ? 'bg-blue-600/20 border-blue-500 ring-1 ring-blue-500/40'
                            : `bg-gray-800/60 ${accent}`
                          }`}
            >
              <div className="text-base leading-none mb-1">{FAULT_ICONS[s.id] ?? '⚙'}</div>
              <div className={`text-xs font-semibold leading-snug ${isSelected ? 'text-blue-300' : 'text-gray-200'}`}>
                {s.name}
              </div>
              <div className="text-xs text-gray-500 mt-0.5 truncate max-w-[110px]">
                {s.machine_type}
              </div>
            </button>
          )
        })}
      </div>

      {/* Selected scenario detail strip */}
      {active && (
        <div className="mt-2 flex items-start gap-2 text-xs text-gray-500 bg-gray-800/50 rounded-lg px-3 py-2 border border-gray-700/50">
          <ChevronRight className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-blue-500" />
          <span><span className="text-gray-400 font-medium">{active.machine_type}: </span>{active.symptom_description}</span>
        </div>
      )}
    </div>
  )
}
