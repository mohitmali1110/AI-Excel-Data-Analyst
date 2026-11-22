// components/InsightCards.jsx
// Displays key insights and recommendations from the agent analysis.

import React from 'react'

export default function InsightCards({ insights, recommendations, keyFindings }) {
  if ((!insights || insights.length === 0) && (!recommendations || recommendations.length === 0)) {
    return null
  }

  return (
    <div className="two-col">
      {/* Key Insights */}
      {insights && insights.length > 0 && (
        <div className="card">
          <h2 className="card-title">
            <span className="icon">💡</span>
            Key Insights
          </h2>

          <div className="insight-list">
            {insights.map((insight, idx) => (
              <div key={idx} className="insight-item">
                <span className="insight-num">{idx + 1}</span>
                <span>{insight}</span>
              </div>
            ))}
          </div>

          {/* Key Findings summary if available */}
          {keyFindings && Object.keys(keyFindings).length > 0 && (
            <div style={{ marginTop: '16px' }}>
              <p className="section-label">Key Numbers</p>
              <div className="stats-grid" style={{ marginBottom: 0 }}>
                {Object.entries(keyFindings).slice(0, 4).map(([key, value]) => (
                  <div key={key} className="stat-box">
                    <span className="stat-value" style={{ fontSize: '1.2rem' }}>
                      {typeof value === 'object' ? JSON.stringify(value).slice(0, 30) : formatValue(value)}
                    </span>
                    <span className="stat-label">
                      {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Recommendations */}
      {recommendations && recommendations.length > 0 && (
        <div className="card">
          <h2 className="card-title">
            <span className="icon">🎯</span>
            Recommendations
          </h2>

          <div className="rec-list">
            {recommendations.map((rec, idx) => (
              <div key={idx} className="rec-item">
                <span className="rec-num">{idx + 1}</span>
                <span>{rec}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

// Helper to format numbers nicely
function formatValue(value) {
  if (typeof value === 'number') {
    if (value > 1000) return value.toLocaleString('en-US', { maximumFractionDigits: 0 })
    return Number(value.toFixed(2)).toLocaleString()
  }
  return String(value)
}
