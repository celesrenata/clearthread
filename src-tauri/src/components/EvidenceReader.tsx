/**
 * EvidenceReader component for Tauri frontend.
 * Displays evidence and source messages.
 */

import React, { useState } from 'react';

interface EvidenceItem {
  id: string;
  type: 'message' | 'image' | 'finding';
  content: string;
  source: string;
  timestamp: string;
}

export function EvidenceReader() {
  const [evidence, setEvidence] = useState<EvidenceItem[]>([]);
  const [filter, setFilter] = useState<'all' | 'message' | 'image' | 'finding'>('all');

  const filteredEvidence = evidence.filter(e => filter === 'all' || e.type === filter);

  return (
    <div className="view-container evidence-reader">
      <h2>Evidence Reader</h2>

      <div className="evidence-filters">
        {(['all', 'message', 'image', 'finding'] as const).map(f => (
          <button
            key={f}
            className={`filter-btn ${filter === f ? 'active' : ''}`}
            onClick={() => setFilter(f)}
          >
            {f.charAt(0).toUpperCase() + f.slice(1)}
          </button>
        ))}
      </div>

      <div className="evidence-list">
        {filteredEvidence.map(item => (
          <div key={item.id} className={`evidence-item ${item.type}`}>
            <div className="evidence-type-badge">{item.type}</div>
            <div className="evidence-content">{item.content}</div>
            <div className="evidence-meta">
              <span>Source: {item.source}</span>
              <span>{item.timestamp}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
