// components/QuestionBox.jsx
// Input area where the user types their question and example chips.

import React, { useState } from 'react'

// Example questions shown as clickable chips below the input
const EXAMPLE_QUESTIONS = [
  'What is the total revenue?',
  'Which category has the highest sales?',
  'Show monthly revenue trend.',
  'Why did revenue decrease?',
  'Which region performed best?',
  'What is the average order value?',
  'What are the most important insights?',
  'Which product generates most revenue?',
]

export default function QuestionBox({ onAsk, loading, disabled, activeFilename }) {
  const [question, setQuestion] = useState('')

  function handleAsk() {
    if (question.trim().length < 3) return
    onAsk(question.trim())
  }

  function handleKeyDown(e) {
    // Submit on Ctrl+Enter or Cmd+Enter
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      handleAsk()
    }
  }

  function selectExample(q) {
    setQuestion(q)
  }

  return (
    <div className="card">
      <h2 className="card-title">
        <span className="icon">💬</span>
        Ask Your Data
      </h2>

      {/* Show which file is active */}
      {activeFilename && !disabled && (
        <div className="alert alert-info" style={{ marginBottom: '16px' }}>
          <span>📄</span>
          <span>
            Analyzing: <strong>{activeFilename}</strong>
          </span>
        </div>
      )}

      {disabled && (
        <div className="alert alert-info" style={{ marginBottom: '16px' }}>
          <span>ℹ️</span>
          <span>Please upload a dataset first before asking questions.</span>
        </div>
      )}

      {/* Text area for the question */}
      <textarea
        className="question-input"
        placeholder="Ask any question about your data... e.g. 'Why did revenue decrease last month?'"
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        onKeyDown={handleKeyDown}
        disabled={disabled || loading}
        rows={3}
      />

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '14px', flexWrap: 'wrap', gap: '12px' }}>
        {/* Analyze button */}
        <button
          className="btn btn-primary btn-large"
          onClick={handleAsk}
          disabled={disabled || loading || question.trim().length < 3}
        >
          {loading ? (
            <>
              <span className="spinner" />
              Agent is analyzing...
            </>
          ) : (
            <>🤖 Analyze with AI Agent</>
          )}
        </button>

        <span style={{ color: 'var(--text-muted)', fontSize: '0.78rem' }}>
          Ctrl+Enter to submit
        </span>
      </div>

      {/* Example question chips */}
      <div style={{ marginTop: '16px' }}>
        <p className="section-label">Example Questions</p>
        <div className="example-questions">
          {EXAMPLE_QUESTIONS.map((q) => (
            <button
              key={q}
              className="example-chip"
              onClick={() => selectExample(q)}
              disabled={disabled || loading}
            >
              {q}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}

