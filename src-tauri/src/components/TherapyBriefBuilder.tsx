/**
 * TherapyBriefBuilder component for Tauri frontend.
 * Allows users to compose therapy session briefs.
 */

import React, { useState } from 'react';

interface BriefSection {
  id: string;
  title: string;
  content: string;
  included: boolean;
}

export function TherapyBriefBuilder() {
  const [sections, setSections] = useState<BriefSection[]>([
    { id: '1', title: 'Relationship Overview', content: '', included: true },
    { id: '2', title: 'Key Episodes', content: '', included: true },
    { id: '3', title: 'Pattern Analysis', content: '', included: true },
    { id: '4', title: 'Growth Insights', content: '', included: false },
    { id: '5', title: 'Reflection Questions', content: '', included: false },
  ]);

  const [briefTitle, setBriefTitle] = useState('Therapy Brief');
  const [notes, setNotes] = useState('');

  const toggleSection = (id: string) => {
    setSections(sections.map(s =>
      s.id === id ? { ...s, included: !s.included } : s
    ));
  };

  const handleExport = async (format: 'markdown' | 'pdf' | 'json') => {
    // In production, call Rust export command
    console.log(`Exporting brief as ${format}`);
  };

  return (
    <div className="view-container brief-builder">
      <h2>Therapy Brief Builder</h2>

      <div className="brief-header">
        <input
          type="text"
          className="brief-title-input"
          value={briefTitle}
          onChange={(e) => setBriefTitle(e.target.value)}
          placeholder="Brief title"
        />
        <div className="export-buttons">
          <button className="btn" onClick={() => handleExport('markdown')}>Markdown</button>
          <button className="btn" onClick={() => handleExport('pdf')}>PDF</button>
          <button className="btn" onClick={() => handleExport('json')}>JSON</button>
        </div>
      </div>

      <div className="brief-content">
        <div className="sections-panel">
          <h3>Sections</h3>
          {sections.map(section => (
            <label key={section.id} className="section-toggle">
              <input
                type="checkbox"
                checked={section.included}
                onChange={() => toggleSection(section.id)}
              />
              <span>{section.title}</span>
            </label>
          ))}
        </div>

        <div className="brief-preview">
          <h3>Preview</h3>
          <div className="preview-content">
            {sections.filter(s => s.included).map(section => (
              <div key={section.id} className="preview-section">
                <h4>{section.title}</h4>
                <p>{section.content || 'Content will appear here...'}</p>
              </div>
            ))}
            <div className="notes-section">
              <h4>Notes</h4>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Add your notes..."
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
