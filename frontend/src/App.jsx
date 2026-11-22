// App.jsx
// Main application component that wires everything together.
//
// State flow:
//   uploadedFiles   → array of ALL uploaded dataset infos
//   activeDataset   → the currently selected dataset (from uploadedFiles)
//   analysisResult  → set when user asks a question and agent responds
//   loading         → true while agent is running
//   error           → any error message to show

import React, { useState } from 'react'
import { askQuestion } from './api.js'

import FileUpload from './components/FileUpload.jsx'
import DatasetPreview from './components/DatasetPreview.jsx'
import QuestionBox from './components/QuestionBox.jsx'
import AgentProgress from './components/AgentProgress.jsx'
import Results from './components/Results.jsx'
import Charts from './components/Charts.jsx'
import InsightCards from './components/InsightCards.jsx'

export default function App() {
  // All uploaded datasets (each is the full response from /upload)
  const [uploadedFiles, setUploadedFiles] = useState([])

  // The currently active dataset the user is working with
  const [activeDataset, setActiveDataset] = useState(null)

  // The full agent response after asking a question
  const [analysisResult, setAnalysisResult] = useState(null)

  // Loading state while agent is processing
  const [loading, setLoading] = useState(false)

  // Error message
  const [error, setError] = useState(null)

  // Called by FileUpload when a new file is successfully uploaded
  function handleUploadSuccess(datasetInfo) {
    setUploadedFiles(prev => {
      // Avoid duplicates: if same filename already in list, replace it
      const exists = prev.findIndex(f => f.filename === datasetInfo.filename)
      if (exists !== -1) {
        const updated = [...prev]
        updated[exists] = datasetInfo
        return updated
      }
      return [...prev, datasetInfo]
    })
    setActiveDataset(datasetInfo)
    setAnalysisResult(null)
    setError(null)
  }

  // Switch the active dataset from the uploaded files list
  function handleSwitchDataset(datasetInfo) {
    setActiveDataset(datasetInfo)
    setAnalysisResult(null)
    setError(null)
  }

  // Remove a file from the uploaded list
  function handleRemoveFile(filename) {
    setUploadedFiles(prev => {
      const updated = prev.filter(f => f.filename !== filename)
      // If we removed the active one, switch to the last remaining
      if (activeDataset?.filename === filename) {
        setActiveDataset(updated.length > 0 ? updated[updated.length - 1] : null)
        setAnalysisResult(null)
      }
      return updated
    })
  }

  // Called by QuestionBox when user clicks Analyze
  async function handleAsk(question) {
    if (!activeDataset) {
      setError('Please upload a dataset first.')
      return
    }

    setLoading(true)
    setError(null)
    setAnalysisResult(null)

    try {
      const result = await askQuestion(activeDataset.filename, question)

      if (!result.success) {
        setError(result.error || 'Analysis failed. Please try again.')
      } else {
        setAnalysisResult(result)
      }
    } catch (err) {
      setError(err.message || 'Something went wrong. Make sure the backend is running.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app">
      {/* ── Header ─────────────────────────────────────────────── */}
      <header className="header">
        <div className="header-brand">
          <div className="header-icon">🤖</div>
          <div>
            <div className="header-title">AI Excel Data Analyst</div>
            <div className="header-subtitle">Agentic AI · Natural Language · Python/Pandas Analysis</div>
          </div>
        </div>
        <div className="header-badge">Final Year Project</div>
      </header>

      {/* ── Main Content ────────────────────────────────────────── */}
      <main className="main-content">

        {/* SECTION 1: File Upload */}
        <FileUpload onUploadSuccess={handleUploadSuccess} />

        {/* SECTION 2: Uploaded Files Switcher (shown when 2+ files uploaded) */}
        {uploadedFiles.length > 1 && (
          <div className="card">
            <h2 className="card-title">
              <span className="icon">📁</span>
              Uploaded Files
              <span style={{
                marginLeft: '10px',
                fontSize: '0.8rem',
                background: 'var(--primary)',
                color: '#fff',
                borderRadius: '12px',
                padding: '2px 10px',
              }}>
                {uploadedFiles.length} files
              </span>
            </h2>
            <div className="uploaded-files-list">
              {uploadedFiles.map((file) => (
                <div
                  key={file.filename}
                  className={`uploaded-file-item ${activeDataset?.filename === file.filename ? 'active' : ''}`}
                  onClick={() => handleSwitchDataset(file)}
                >
                  <div className="uploaded-file-info">
                    <span className="uploaded-file-icon">
                      {file.original_filename?.endsWith('.xlsx') ? '📗' : '📄'}
                    </span>
                    <div>
                      <div className="uploaded-file-name">{file.original_filename}</div>
                      <div className="uploaded-file-meta">
                        {file.rows?.toLocaleString()} rows · {file.columns} cols
                      </div>
                    </div>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    {activeDataset?.filename === file.filename && (
                      <span className="active-badge">Active</span>
                    )}
                    <button
                      className="remove-file-btn"
                      title="Remove file"
                      onClick={(e) => {
                        e.stopPropagation()
                        handleRemoveFile(file.filename)
                      }}
                    >
                      ✕
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* SECTION 3: Dataset Preview (shown after upload) */}
        {activeDataset && (
          <DatasetPreview datasetInfo={activeDataset} />
        )}

        {/* SECTION 4: Question Box */}
        <QuestionBox
          onAsk={handleAsk}
          loading={loading}
          disabled={!activeDataset}
          activeFilename={activeDataset?.original_filename}
        />

        {/* SECTION 5: Error display */}
        {error && (
          <div className="alert alert-error">
            <span>⚠️</span>
            <span>{error}</span>
          </div>
        )}

        {/* SECTION 6: Agent Progress (shown while loading or after result) */}
        {(loading || analysisResult) && (
          <AgentProgress
            agentSteps={analysisResult?.agent_steps}
            isLoading={loading}
            plan={analysisResult?.plan}
            toolsUsed={analysisResult?.tools_used}
          />
        )}

        {/* SECTION 7–9: Results (shown only after successful analysis) */}
        {analysisResult && (
          <>
            {/* Final Answer + Reflection */}
            <Results result={analysisResult} />

            {/* Insight Cards + Recommendations */}
            <InsightCards
              insights={analysisResult.insights}
              recommendations={analysisResult.recommendations}
              keyFindings={analysisResult.key_findings}
            />

            {/* Charts */}
            <Charts charts={analysisResult.charts} />
          </>
        )}
      </main>

      {/* ── Footer ─────────────────────────────────────────────── */}
      <footer className="footer">
        <p>AI Excel Data Analyst · Final Year B.Tech Project · Agentic AI System</p>
        <p style={{ marginTop: '4px' }}>
          Built with React · FastAPI · Pandas · Matplotlib · OpenAI API
        </p>
      </footer>
    </div>
  )
}
