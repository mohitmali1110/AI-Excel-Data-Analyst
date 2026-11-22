// api.js
// All API calls to the FastAPI backend are centralised here.
// The BASE_URL points to the backend running locally.

const BASE_URL = 'http://localhost:8000'

/**
 * Upload a CSV or XLSX file to the backend.
 * @param {File} file - The file object selected by the user.
 * @returns {Promise<Object>} - Dataset info response from backend.
 */
export async function uploadFile(file) {
  const formData = new FormData()
  formData.append('file', file)

  const response = await fetch(`${BASE_URL}/upload`, {
    method: 'POST',
    body: formData,
    // Note: Do NOT set Content-Type manually for FormData — browser sets it automatically
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'File upload failed')
  }

  return response.json()
}

/**
 * Ask a natural language question about the uploaded dataset.
 * This triggers the full AI agent workflow on the backend.
 *
 * @param {string} filename - The filename returned by uploadFile.
 * @param {string} question - The user's question.
 * @returns {Promise<Object>} - Agent response with answer, insights, charts, etc.
 */
export async function askQuestion(filename, question) {
  const response = await fetch(`${BASE_URL}/ask`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ filename, question }),
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || error.error || 'Analysis failed')
  }

  return response.json()
}

/**
 * Get dataset info for an already-uploaded file.
 * @param {string} filename - The saved filename.
 * @returns {Promise<Object>} - Dataset inspection data.
 */
export async function getDatasetInfo(filename) {
  const response = await fetch(`${BASE_URL}/dataset/${filename}`)

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Could not load dataset info')
  }

  return response.json()
}

/**
 * Get the full URL for a generated chart image.
 * @param {string} filename - The chart filename (e.g. "chart_bar_abc123.png").
 * @returns {string} - Full URL to the chart image.
 */
export function getChartUrl(filename) {
  return `${BASE_URL}/charts/${filename}`
}
