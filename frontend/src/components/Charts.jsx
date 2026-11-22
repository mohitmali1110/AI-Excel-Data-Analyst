// components/Charts.jsx
// Displays generated chart images returned by the backend.

import React from 'react'
import { getChartUrl } from '../api.js'

export default function Charts({ charts }) {
  if (!charts || charts.length === 0) return null

  return (
    <div className="card">
      <h2 className="card-title">
        <span className="icon">📈</span>
        Charts & Visualizations
      </h2>

      <div className="charts-grid">
        {charts.map((chart, idx) => {
          // chart.filename is like "chart_bar_abc123.png"
          // chart.url is like "/charts/chart_bar_abc123.png"
          const imageUrl = getChartUrl(chart.filename)

          return (
            <div key={idx} className="chart-card">
              <div className="chart-title">
                {chart.title || `Chart ${idx + 1}`}
                <span style={{
                  marginLeft: '8px',
                  padding: '2px 8px',
                  background: 'rgba(108,99,255,0.15)',
                  borderRadius: '10px',
                  fontSize: '0.7rem',
                  color: 'var(--accent-light)',
                }}>
                  {chart.chart_type}
                </span>
              </div>

              <img
                src={imageUrl}
                alt={chart.title || `Chart ${idx + 1}`}
                className="chart-img"
                onError={(e) => {
                  // If image fails to load, show a placeholder
                  e.target.style.display = 'none'
                  e.target.nextSibling.style.display = 'flex'
                }}
              />

              {/* Fallback if image doesn't load */}
              <div style={{
                display: 'none',
                height: '200px',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'var(--text-muted)',
                fontSize: '0.85rem',
              }}>
                ⚠️ Chart could not be loaded
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
