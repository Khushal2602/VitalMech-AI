import { useState } from 'react'
import axios from 'axios'

/**
 * useDiagnosis — custom hook for calling POST /api/diagnose
 *
 * Returns: { diagnose, result, isLoading, agentStep, error, reset }
 * agentStep: 0 = idle, 1–4 = agents in progress, 5 = complete
 */
export function useDiagnosis() {
  const [result, setResult] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  const [agentStep, setAgentStep] = useState(0)
  const [error, setError] = useState(null)

  const diagnose = async (sensorData) => {
    setIsLoading(true)
    setResult(null)
    setError(null)
    setAgentStep(1)

    // Simulate agent step progression during the API call
    const stepTimers = []
    stepTimers.push(setTimeout(() => setAgentStep(2), 800))
    stepTimers.push(setTimeout(() => setAgentStep(3), 1800))
    stepTimers.push(setTimeout(() => setAgentStep(4), 2800))

    try {
      const response = await axios.post('/api/diagnose', sensorData)
      clearTimeout(stepTimers[0])
      clearTimeout(stepTimers[1])
      clearTimeout(stepTimers[2])
      setAgentStep(5)
      setResult(response.data)
    } catch (err) {
      clearTimeout(stepTimers[0])
      clearTimeout(stepTimers[1])
      clearTimeout(stepTimers[2])
      setAgentStep(0)
      setError(
        err.response?.data?.detail ||
          err.message ||
          'An unknown error occurred. Check that the backend is running.'
      )
    } finally {
      setIsLoading(false)
    }
  }

  const reset = () => {
    setResult(null)
    setError(null)
    setAgentStep(0)
    setIsLoading(false)
  }

  return { diagnose, result, isLoading, agentStep, error, reset }
}
