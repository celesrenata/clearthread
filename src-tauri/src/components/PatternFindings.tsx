/**
 * PatternFindings component for Tauri frontend.
 * Displays interaction pattern findings.
 */

import React, { useState } from 'react';

interface Finding {
  id: string;
  title: string;
  description: string;
  confidence: number;
  evidence_count: number;
  category: string;
}

export function PatternFindings() {
  const [findings, setFindings] = useState<Finding[]>([]);
  const [selectedFinding, setSelectedFinding] = useState<Finding | null>(null);

  return (
    <div className="view-container pattern-findings">
      <h2>Pattern Findings</h2>

      <div className="findings-layout">
        <div className="findings-list">
          {findings.map(finding => (
            <div
              key={finding.id}
              className={`finding-card ${selectedFinding?.id === finding.id ? 'selected' : ''}`}
              onClick={() => setSelectedFinding(finding)}
            >
              <h3>{finding.title}</h3>
              <p>{finding.description}</p>
              <div className="finding-meta">
                <span className="confidence">{Math.round(finding.confidence * 100)}%</span>
                <span className="evidence">{finding.evidence_count} evidence</span>
                <span className="category">{finding.category}</span>
              </div>
            </div>
          ))}
        </div>

        {selectedFinding && (
          <div className="finding-detail">
            <h3>{selectedFinding.title}</h3>
            <p>{selectedFinding.description}</p>
            <div className="detail-meta">
              <span>Confidence: {Math.round(selectedFinding.confidence * 100)}%</span>
              <span>Evidence: {selectedFinding.evidence_count}</span>
              <span>Category: {selectedFinding.category}</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
