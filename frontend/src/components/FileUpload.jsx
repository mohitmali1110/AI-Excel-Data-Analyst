// components/FileUpload.jsx
// Component for uploading CSV/XLSX files.
// Shows a drag-and-drop zone, file picker, and upload status.

import React, { useState, useRef } from 'react'
import { uploadFile } from '../api.js'

export default function FileUpload({ onUploadSuccess }) {
  const [selectedFile, setSelectedFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [dragOver, setDragOver] = useState(false)
  const fileInputRef = useRef(null)

  // Handle file selection from input
  function handleFileChange(e) {
    const file = e.target.files[0]
    if (file) {
      setSelectedFile(file)
      setError(null)
    }
  }

  // Handle drag-over event
  function handleDragOver(e) {
    e.preventDefault()
    setDragOver(true)
  }

  function handleDragLeave() {
    setDragOver(false)
  }

  // Handle file drop
  function handleDrop(e) {
    e.preventDefault()
    setDragOver(false)
    const file = e.dataTransfer.files[0]
    if (file) {
      setSelectedFile(file)
      setError(null)
    }
  }

  // Upload the selected file to the backend
  async function handleUpload() {
    if (!selectedFile) {
      setError('Please select a file first.')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const result = await uploadFile(selectedFile)
      // Pass the result up to the parent component (App.jsx)
      onUploadSuccess(result)
    } catch (err) {
      setError(err.message || 'Upload failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  // Trigger file input click when zone is clicked
  function handleZoneClick() {
    fileInputRef.current?.click()
  }

  return (
    <div className="card">
      <h2 className="card-title">
        <span className="icon">📂</span>
        Upload Your Dataset
      </h2>

      {/* Drag & Drop Zone */}
      <div
        className={`upload-zone ${dragOver ? 'drag-over' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={handleZoneClick}
        style={{ cursor: 'pointer' }}
      >
        <span className="upload-icon">🗂️</span>
        <p className="upload-text">
          Drag & drop your file here, or <strong>click to browse</strong>
        </p>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>
          Supports: <strong>.csv</strong> and <strong>.xlsx</strong> — Max 20 MB
        </p>

        {/* Hidden file input */}
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv,.xlsx"
          onChange={handleFileChange}
          style={{ display: 'none' }}
        />
      </div>

      {/* Selected file name */}
      {selectedFile && (
        <div className="alert alert-info" style={{ marginTop: '14px' }}>
          <span>📄</span>
          <span>
            <strong>{selectedFile.name}</strong>
            &nbsp;({(selectedFile.size / 1024).toFixed(1)} KB) — Ready to upload
          </span>
        </div>
      )}

      {/* Error message */}
      {error && (
        <div className="alert alert-error" style={{ marginTop: '14px' }}>
          <span>⚠️</span>
          <span>{error}</span>
        </div>
      )}

      {/* Upload button */}
      <div className="upload-row" style={{ marginTop: '16px' }}>
        <button
          className="btn btn-primary btn-large"
          onClick={handleUpload}
          disabled={!selectedFile || loading}
        >
          {loading ? (
            <>
              <span className="spinner" />
              Uploading & Analyzing...
            </>
          ) : (
            <>⬆️ Upload & Inspect Dataset</>
          )}
        </button>

        {selectedFile && (
          <button
            className="btn btn-secondary"
            onClick={() => {
              setSelectedFile(null)
              setError(null)
              if (fileInputRef.current) fileInputRef.current.value = ''
            }}
          >
            ✕ Clear
          </button>
        )}
      </div>
    </div>
  )
}
