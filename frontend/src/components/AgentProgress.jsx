// components/AgentProgress.jsx
// Displays the agent's step-by-step workflow as it runs.
// This makes the agentic behavior VISIBLE to the user.

import React from 'react'

// Icons for each step type
function getStepIcon(stepName, status) {
  if (status === 'in_progress') return '⚙️'
  const name = stepName.toLowerCase()
  if (name.includes('inspect') || name.includes('dataset')) return '🔍'
  if (name.includes('clean')) return '🧹'
  if (name.includes('question') || name.includes('understand')) return '🧠'
  if (name.includes('plan')) return '📋'
  if (name.includes('tool')) return '🔧'
  if (name.includes('analysis') || name.includes('pandas') || name.includes('python')) return '⚗️'
  if (name.includes('reflection') || name.includes('reflect')) return '🔄'
  if (name.includes('additional')) return '🔃'
  if (name.includes('insight')) return '💡'
  if (name.includes('chart') || name.includes('visual')) return '📊'
  if (name.includes('final') || name.includes('answer')) return '✅'
  return '▶️'
}

export default function AgentProgress({ agentSteps, isLoading, plan, toolsUsed }) {
  if (!agentSteps && !isLoading) return null

  return (
    <div className="card">
      <h2 className="card-title">
        <span className="icon">🤖</span>
        Agent Workflow
        {isLoading && <span className="spinner" style={{ marginLeft: 'auto' }} />}
      </h2>

      {/* Analysis Plan */}
      {plan && plan.length > 0 && (
        <div style={{ marginBottom: '20px' }}>
          <p className="section-label">📋 Analysis Plan</p>
          <div className="plan-list">
            {plan.map((step, idx) => (
              <div key={idx} className="plan-item">
                <span className="plan-num">{idx + 1}.</span>
                <span>{step}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tools Selected */}
      {toolsUsed && toolsUsed.length > 0 && (
        <div style={{ marginBottom: '20px' }}>
          <p className="section-label">🔧 Tools Selected</p>
          <div className="tools-used">
            {toolsUsed.map((tool) => (
              <span key={tool} className="tool-pill">
                {tool}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Step-by-step execution log */}
      {agentSteps && agentSteps.length > 0 && (
        <div>
          <p className="section-label">⚙️ Execution Log</p>
          <div className="progress-steps">
            {agentSteps.map((step, idx) => (
              <div
                key={idx}
                className={`progress-step ${step.status}`}
              >
                <span className="step-icon">
                  {getStepIcon(step.step, step.status)}
                </span>
                <div style={{ flex: 1 }}>
                  <div className="step-name">{step.step}</div>
                  {step.detail && (
                    <div className="step-detail">{step.detail}</div>
                  )}
                </div>
                {step.timestamp && (
                  <span className="step-time">{step.timestamp}</span>
                )}
              </div>
            ))}

            {/* Show spinning indicator for last step if still loading */}
            {isLoading && (
              <div className="progress-step in_progress">
                <span className="step-icon">⚙️</span>
                <div style={{ flex: 1 }}>
                  <div className="step-name">Processing...</div>
                  <div className="step-detail">AI agent is working on your question</div>
                </div>
                <span className="spinner" />
              </div>
            )}
          </div>
        </div>
      )}

      {/* Empty state while loading */}
      {isLoading && (!agentSteps || agentSteps.length === 0) && (
        <div className="progress-steps">
          <div className="progress-step in_progress">
            <span className="step-icon">⚙️</span>
            <div style={{ flex: 1 }}>
              <div className="step-name">Initializing Agent...</div>
              <div className="step-detail">Preparing dataset and analysis pipeline</div>
            </div>
            <span className="spinner" />
          </div>
        </div>
      )}
    </div>
  )
}
