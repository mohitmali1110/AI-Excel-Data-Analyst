// components/DatasetPreview.jsx
// Shows dataset statistics (rows, columns, missing values) and a preview table.

import React, { useState } from 'react'

export default function DatasetPreview({ datasetInfo }) {
  const [showAllCols, setShowAllCols] = useState(false)

  if (!datasetInfo) return null

  const {
    rows, columns, column_names, column_dtypes,
    missing_values, total_missing, duplicates,
    numeric_columns, categorical_columns, date_columns,
    preview, original_filename,
  } = datasetInfo

  // Columns to display in the preview table
  const displayCols = showAllCols ? column_names : column_names?.slice(0, 8)

  return (
    <div className="card">
      <h2 className="card-title">
        <span className="icon">📊</span>
        Dataset Overview — {original_filename}
      </h2>

      {/* Stats Row */}
      <div className="stats-grid">
        <div className="stat-box">
          <span className="stat-value">{rows?.toLocaleString()}</span>
          <span className="stat-label">Rows</span>
        </div>
        <div className="stat-box">
          <span className="stat-value">{columns}</span>
          <span className="stat-label">Columns</span>
        </div>
        <div className="stat-box">
          <span className="stat-value" style={{ color: total_missing > 0 ? 'var(--warning)' : 'var(--success)' }}>
            {total_missing}
          </span>
          <span className="stat-label">Missing Values</span>
        </div>
        <div className="stat-box">
          <span className="stat-value" style={{ color: duplicates > 0 ? 'var(--danger)' : 'var(--success)' }}>
            {duplicates}
          </span>
          <span className="stat-label">Duplicates</span>
        </div>
        <div className="stat-box">
          <span className="stat-value">{numeric_columns?.length || 0}</span>
          <span className="stat-label">Numeric Cols</span>
        </div>
        <div className="stat-box">
          <span className="stat-value">{categorical_columns?.length || 0}</span>
          <span className="stat-label">Category Cols</span>
        </div>
      </div>

      {/* Column Classification */}
      <div style={{ marginBottom: '20px' }}>
        <p className="section-label">Column Types</p>
        <div className="tag-list">
          {numeric_columns?.map(col => (
            <span key={col} className="tag tag-numeric">📈 {col}</span>
          ))}
          {categorical_columns?.map(col => (
            <span key={col} className="tag tag-categorical">🏷️ {col}</span>
          ))}
          {date_columns?.map(col => (
            <span key={col} className="tag tag-date">📅 {col}</span>
          ))}
        </div>
      </div>

      {/* Missing Values Detail */}
      {missing_values && Object.keys(missing_values).length > 0 && (
        <div style={{ marginBottom: '20px' }}>
          <p className="section-label">Missing Values by Column</p>
          <div className="tag-list">
            {Object.entries(missing_values).map(([col, count]) => (
              <span key={col} style={{
                padding: '3px 10px',
                background: 'rgba(255,107,107,0.1)',
                border: '1px solid rgba(255,107,107,0.3)',
                borderRadius: '12px',
                fontSize: '0.75rem',
                color: 'var(--danger)',
              }}>
                {col}: {count}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Data Preview Table */}
      {preview && preview.length > 0 && (
        <>
          <p className="section-label">Data Preview (first {preview.length} rows)</p>
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  {displayCols?.map(col => (
                    <th key={col}>
                      {col}
                      <span style={{ color: 'var(--text-muted)', fontSize: '0.7rem', marginLeft: '4px' }}>
                        ({column_dtypes?.[col] || ''})
                      </span>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {preview.map((row, rowIdx) => (
                  <tr key={rowIdx}>
                    {displayCols?.map(col => (
                      <td key={col}>
                        {row[col] === null || row[col] === undefined
                          ? <span style={{ color: 'var(--danger)', fontSize: '0.75rem' }}>NULL</span>
                          : String(row[col])}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {column_names?.length > 8 && (
            <button
              className="btn btn-secondary"
              style={{ marginTop: '12px', fontSize: '0.8rem' }}
              onClick={() => setShowAllCols(!showAllCols)}
            >
              {showAllCols ? '← Show fewer columns' : `Show all ${column_names.length} columns →`}
            </button>
          )}
        </>
      )}
    </div>
  )
}
