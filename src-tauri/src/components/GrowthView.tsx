/**
 * GrowthView component for Tauri frontend.
 * Displays growth and resilience analysis.
 */

import React, { useState } from 'react';

interface GrowthFinding {
  id: string;
  title: string;
  description: string;
  category: string;
  strength: number;
  timeline: { date: string; event: string }[];
}

export function GrowthView() {
  const [findings, setFindings] = useState<GrowthFinding[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');

  const categories = ['all', 'resilience', 'communication', 'support', 'growth'];

  const filteredFindings = findings.filter(f =>
    selectedCategory === 'all' || f.category === selectedCategory
  );

  return (
    <div className="view-container growth-view">
      <h2>Growth & Resilience</h2>

      <div className="category-filters">
        {categories.map(cat => (
          <button
            key={cat}
            className={`category-btn ${selectedCategory === cat ? 'active' : ''}`}
            onClick={() => setSelectedCategory(cat)}
          >
            {cat.charAt(0).toUpperCase() + cat.slice(1)}
          </button>
        ))}
      </div>

      <div className="growth-grid">
        {filteredFindings.map(finding => (
          <div key={finding.id} className="growth-card">
            <div className="growth-header">
              <h3>{finding.title}</h3>
              <div className="strength-meter">
                <div className="strength-bar" style={{ width: `${finding.strength * 100}%` }} />
              </div>
            </div>
            <p>{finding.description}</p>
            <div className="growth-timeline">
              {finding.timeline.map((item, i) => (
                <div key={i} className="timeline-item">
                  <span className="timeline-date">{item.date}</span>
                  <span className="timeline-event">{item.event}</span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
