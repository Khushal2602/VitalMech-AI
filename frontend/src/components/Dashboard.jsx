import { useState } from 'react'
import { useDiagnosis } from '../hooks/useDiagnosis'
import SENSOR_PRESETS from '../data/sensorPresets'
import ScenarioSelector from './ScenarioSelector'
import SensorPanel from './SensorPanel'
import AgentTimeline from './AgentTimeline'
import FaultCard from './FaultCard'
import RepairGuidance from './RepairGuidance'
import HealthScoreBar from './HealthScoreBar'
import { Activity, Cpu, AlertTriangle } from 'lucide-react'

export default function Dashboard() {
  const [selectedScenario, setSelectedScenario] = useState(null)
  const { diagnose, result, isLoading, agentStep, error, reset } = useDiagnosis()

  const handleScenarioChange = (scenarioId) => {
    const scenario = SENSOR_PRESETS.find((s) => s.id === scenarioId)
    setSelectedScenario(scenario || null)
    reset()
  }

  const handleDiagnose = () => {
    if (!selectedScenario) return
    diagnose({
      scenario_id: selectedScenario.id,
      machine_type: selectedScenario.machine_type,
      symptom_description: selectedScenario.symptom_description,
      sensors: selectedScenario.sensors,
    })
  }

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100" style={{ fontFamily: "'Inter', system-ui, sans-serif" }}>

      {/* ── Header ── */}
      <header className="border-b border-gray-800 bg-gray-900/80 backdrop-blur-sm sticky top-0 z-20">
        <div className="max-w-7xl mx-auto px-6 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="bg-blue-600 rounded-lg p-1.5 flex items-center justify-center">
              <Activity className="w-5 h-5 text-white" />
            </div>
            <div>
              <span className="text-lg font-bold text-white tracking-tight">VitalMech</span>
              <span className="ml-2 text-xs text-gray-500 font-normal hidden sm:inline">
                AI-Powered Mechanical Fault Diagnosis
              </span>
            </div>
          </div>

          <div className="flex items-center gap-4">
            {/* AI source badge — shown after diagnosis */}
            {result && (
              <span className={`hidden sm:inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full border font-medium ${
                result.ai_source === 'granite'
                  ? 'bg-blue-950 border-blue-700 text-blue-300'
                  : 'bg-gray-800 border-gray-600 text-gray-400'
              }`}>
                <Cpu className="w-3 h-3" />
                {result.ai_source === 'granite' ? `IBM Granite · ${result.model_used}` : 'Rule-Based Engine'}
              </span>
            )}
            <div className="flex items-center gap-1.5 text-xs text-gray-500">
              <span className="w-2 h-2 rounded-full bg-green-500 inline-block animate-pulse" />
              System Online
            </div>
          </div>
        </div>
      </header>

      {/* ── Main ── */}
      <main className="max-w-7xl mx-auto px-6 py-6">

        {/* Scenario selector + run button */}
        <div className="flex flex-col sm:flex-row gap-3 items-start sm:items-end mb-6">
          <div className="flex-1 min-w-0">
            <ScenarioSelector
              scenarios={SENSOR_PRESETS}
              selected={selectedScenario?.id || ''}
              onChange={handleScenarioChange}
            />
          </div>
          <button
            onClick={handleDiagnose}
            disabled={!selectedScenario || isLoading}
            className="flex items-center gap-2 px-5 py-2.5 rounded-lg bg-blue-600 text-white
                       text-sm font-semibold hover:bg-blue-500 active:bg-blue-700
                       disabled:opacity-40 disabled:cursor-not-allowed
                       transition-colors whitespace-nowrap flex-shrink-0"
          >
            <Activity className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
            {isLoading ? 'Analyzing…' : 'Run Diagnosis'}
          </button>
        </div>

        {/* Error banner */}
        {error && (
          <div className="mb-5 rounded-xl border border-red-700 bg-red-950/60 px-4 py-3
                          flex items-start gap-3 text-sm text-red-300">
            <AlertTriangle className="w-4 h-4 mt-0.5 flex-shrink-0 text-red-400" />
            <div>
              <span className="font-semibold">Diagnosis failed — </span>{error}
            </div>
          </div>
        )}

        {/* Health score strip — only when result available */}
        {result && (
          <div className="mb-5">
            <HealthScoreBar result={result} />
          </div>
        )}

        {/* ── Two-column grid ── */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">

          {/* Left column */}
          <div className="flex flex-col gap-5">
            <SensorPanel sensors={selectedScenario?.sensors ?? null} />
            <AgentTimeline agentStep={agentStep} isLoading={isLoading} result={result} />
          </div>

          {/* Right column */}
          <div className="lg:col-span-2 flex flex-col gap-5">
            <FaultCard result={result} isLoading={isLoading} />
            <RepairGuidance result={result} isLoading={isLoading} />
          </div>
        </div>

      </main>

      {/* ── Footer ── */}
      <footer className="border-t border-gray-800 mt-12 py-4 text-center text-xs text-gray-600">
        VitalMech · Problem Statement #34 · IBM Granite · Hackathon 2025
      </footer>
    </div>
  )
}
