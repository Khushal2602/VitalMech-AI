import { Thermometer, Zap, Gauge, Activity, Volume2, Wind } from 'lucide-react'

const SENSOR_CONFIGS = [
  {
    key: 'rpm',
    label: 'Speed',
    unit: 'RPM',
    icon: Wind,
    max: 4000,
    thresholds: { warn: 3200, danger: 3500 },
    inverted: false,
  },
  {
    key: 'temperature_c',
    label: 'Temperature',
    unit: '°C',
    icon: Thermometer,
    max: 130,
    thresholds: { warn: 75, danger: 90 },
    inverted: false,
  },
  {
    key: 'vibration_mm_s',
    label: 'Vibration',
    unit: 'mm/s',
    icon: Activity,
    max: 20,
    thresholds: { warn: 7.1, danger: 11.0 },
    inverted: false,
  },
  {
    key: 'pressure_bar',
    label: 'Pressure',
    unit: 'bar',
    icon: Gauge,
    max: 10,
    thresholds: { warn: 2.0, danger: 1.5 },
    inverted: true,
  },
  {
    key: 'current_amps',
    label: 'Current',
    unit: 'A',
    icon: Zap,
    max: 60,
    thresholds: { warn: 35, danger: 44 },
    inverted: false,
  },
  {
    key: 'noise_db',
    label: 'Noise',
    unit: 'dB',
    icon: Volume2,
    max: 110,
    thresholds: { warn: 80, danger: 90 },
    inverted: false,
  },
]

function getStatus(config, value) {
  if (value === null || value === undefined) return 'idle'
  if (config.inverted) {
    if (value <= config.thresholds.danger) return 'danger'
    if (value <= config.thresholds.warn) return 'warn'
    return 'normal'
  }
  if (value >= config.thresholds.danger) return 'danger'
  if (value >= config.thresholds.warn) return 'warn'
  return 'normal'
}

const STATUS_RING = {
  idle:   'border-gray-700',
  normal: 'border-gray-700',
  warn:   'border-yellow-600',
  danger: 'border-red-600',
}
const STATUS_VALUE_COLOR = {
  idle:   'text-gray-600',
  normal: 'text-gray-100',
  warn:   'text-yellow-300',
  danger: 'text-red-300',
}
const STATUS_BAR = {
  idle:   'bg-gray-700',
  normal: 'bg-green-500',
  warn:   'bg-yellow-500',
  danger: 'bg-red-500',
}
const STATUS_BG = {
  idle:   '',
  normal: '',
  warn:   'bg-yellow-950/20',
  danger: 'bg-red-950/20',
}

export default function SensorPanel({ sensors }) {
  const hasData = sensors !== null && sensors !== undefined

  return (
    <div>
      <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
        Sensor Readings (Simulated)
      </h2>
      <div className="grid grid-cols-2 gap-2.5">
        {SENSOR_CONFIGS.map((config) => {
          const value  = sensors?.[config.key] ?? null
          const status = getStatus(config, value)
          const Icon   = config.icon
          const pct    = value !== null ? Math.min(100, Math.round((value / config.max) * 100)) : 0

          return (
            <div
              key={config.key}
              className={`rounded-xl border p-3 transition-colors duration-300
                          ${STATUS_RING[status]} ${STATUS_BG[status]} bg-gray-800/80`}
            >
              {/* Header row */}
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-1.5">
                  <Icon className={`w-3.5 h-3.5 ${
                    status === 'idle' ? 'text-gray-600' :
                    status === 'danger' ? 'text-red-400' :
                    status === 'warn' ? 'text-yellow-400' : 'text-gray-400'
                  }`} />
                  <span className="text-xs text-gray-500">{config.label}</span>
                </div>
                {/* Status dot */}
                {status !== 'idle' && (
                  <span className={`w-1.5 h-1.5 rounded-full ${
                    status === 'danger' ? 'bg-red-500 animate-pulse' :
                    status === 'warn'   ? 'bg-yellow-500' : 'bg-green-500'
                  }`} />
                )}
              </div>

              {/* Value */}
              <div className={`text-2xl font-bold tabular-nums leading-none mb-2 ${STATUS_VALUE_COLOR[status]}`}>
                {value !== null ? value : '—'}
                <span className="text-xs font-normal text-gray-600 ml-1">{config.unit}</span>
              </div>

              {/* Mini bar chart */}
              <div className="h-1 rounded-full bg-gray-700 overflow-hidden">
                <div
                  className={`h-1 rounded-full transition-all duration-500 ${hasData ? STATUS_BAR[status] : 'bg-gray-700'}`}
                  style={{ width: hasData ? `${pct}%` : '0%' }}
                />
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
