/**
 * ExportCenter component for Tauri frontend.
 * Handles all export operations.
 */

import React, { useState } from 'react';

export function ExportCenter() {
  const [isExporting, setIsExporting] = useState(false);
  const [progress, setProgress] = useState(0);
  const [exportHistory, setExportHistory] = useState<ExportRecord[]>([]);

  interface ExportRecord {
    id: string;
    format: string;
    date: string;
    path: string;
  }

  const handleExport = async (format: 'markdown' | 'pdf' | 'json') => {
    setIsExporting(true);
    setProgress(0);

    // Simulate export progress
    const interval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 100) {
          clearInterval(interval);
          setIsExporting(false);
          return 100;
        }
        return prev + 10;
      });
    }, 200);

    // In production, call Rust export command
    // const result = await invoke('export_markdown', { format });
  };

  return (
    <div className="view-container export-center">
      <h2>Export Center</h2>

      <div className="export-options">
        <button
          className="export-btn"
          onClick={() => handleExport('markdown')}
          disabled={isExporting}
        >
          <span className="export-icon">📝</span>
          <span>Export as Markdown</span>
        </button>

        <button
          className="export-btn"
          onClick={() => handleExport('pdf')}
          disabled={isExporting}
        >
          <span className="export-icon">📄</span>
          <span>Export as PDF</span>
        </button>

        <button
          className="export-btn"
          onClick={() => handleExport('json')}
          disabled={isExporting}
        >
          <span className="export-icon">🔧</span>
          <span>Export as JSON</span>
        </button>
      </div>

      {isExporting && (
        <div className="export-progress">
          <div className="progress-bar">
            <div className="progress-fill" style={{ width: `${progress}%` }} />
          </div>
          <p>Exporting... {progress}%</p>
        </div>
      )}

      {exportHistory.length > 0 && (
        <div className="export-history">
          <h3>Recent Exports</h3>
          <ul>
            {exportHistory.map(record => (
              <li key={record.id}>
                <span>{record.format.toUpperCase()}</span>
                <span>{record.date}</span>
                <span>{record.path}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
