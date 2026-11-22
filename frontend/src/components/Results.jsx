// components/Results.jsx
// Displays the final answer, reflection, and analysis summary.

import React, { useState } from 'react'

export default function Results({ result }) {
  const [showRawResults, setShowRawResults] = useState(false)

  if (!result) return null

  const { question, answer, reflection, reflection_log, analysis_results, cleaning_summary } = result

  return (
    <div className="card">
      <h2 className="card-title">
        <span className="icon">📝</span>
        Analysis Results
      </h2>

      {/* Question asked */}
      <div style={{ marginBottom: '20px' }}>
        <p className="section-label">Question Asked</p>
        <div style={{
          padding: '12px 16px',
          background: 'var(--bg-secondary)',
          borderRadius: 'var(--radius-sm)',
          border: '1px solid var(--border)',
          color: 'var(--text-secondary)',
          fontStyle: 'italic',
          fontSize: '0.95rem',
        }}>
          "{question}"
        </div>
      </div>

      {/* Final Answer */}
      <div style={{ marginBottom: '20px' }}>
        <p className="section-label">✅ Final Answer</p>
        <div className="answer-box">{answer}</div>
      </div>

      {/* Reflection Log */}
      {reflection_log && reflection_log.length > 0 && (
        <div style={{ marginBottom: '20px' }}>
          <p className="section-label">🔄 Agent Reflection</p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {reflection_log.map((log, idx) => (
              <div key={idx} className="reflection-box">
                <strong>Loop {log.loop}:</strong> {log.reason}
                {!log.sufficient && log.additional_analysis?.length > 0 && (
                  <span style={{ color: 'var(--accent-2)', marginLeft: '8px' }}>
                    → Running additional: {log.additional_analysis.join(', ')}
                  </span>
                )}
                {log.sufficient && (
                  <span style={{ color: 'var(--success)', marginLeft: '8px' }}>
                    ✓ Sufficient
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Cleaning Summary */}
      {cleaning_summary && cleaning_summary.actions_taken?.length > 0 && (
        <div style={{ marginBottom: '20px' }}>
          <p className="section-label">🧹 Data Cleaning Performed</p>
          <div style={{
            background: 'var(--bg-secondary)',
            border: '1px solid var(--border)',
            borderRadius: 'var(--radius-sm)',
            padding: '14px 16px',
          }}>
            {cleaning_summary.actions_taken.map((action, idx) => (
              <div key={idx} style={{ fontSize: '0.84rem', color: 'var(--text-secondary)', marginBottom: '4px' }}>
                • {action}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Raw Analysis Results toggle */}
      {analysis_results && analysis_results.length > 0 && (
        <div>
          <button
            className="btn btn-secondary"
            style={{ fontSize: '0.8rem' }}
            onClick={() => setShowRawResults(!showRawResults)}
          >
            {showRawResults ? '▲ Hide' : '▼ Show'} Raw Analysis Data ({analysis_results.length} result{analysis_results.length !== 1 ? 's' : ''})
          </button>

          {showRawResults && (
            <div style={{
              marginTop: '12px',
              background: 'var(--bg-secondary)',
              border: '1px solid var(--border)',
              borderRadius: 'var(--radius-sm)',
              padding: '14px',
              maxHeight: '400px',
              overflowY: 'auto',
            }}>
              <pre style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                {JSON.stringify(analysis_results, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
