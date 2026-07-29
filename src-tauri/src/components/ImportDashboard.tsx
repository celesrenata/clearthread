/**
 * ImportDashboard component for Tauri frontend.
 * Handles the import flow with progress tracking.
 */

import React, { useState } from 'react';
import { invoke } from '@tauri-apps/api/core';

interface ImportDashboardProps {
  onComplete?: () => void;
}

export function ImportDashboard({ onComplete }: ImportDashboardProps) {
  const [isImporting, setIsImporting] = useState(false);
  const [progress, setProgress] = useState(0);
  const [currentFile, setCurrentFile] = useState('');
  const [errors, setErrors] = useState<string[]>([]);
  const [importResult, setImportResult] = useState<ImportResult | null>(null);

  interface ImportResult {
    batch_id: string;
    messages: number;
    conversations: number;
    participants: number;
    attachments: number;
    duplicates: number;
    encoding_fixes: number;
  }

  const handleImport = async (isZip: boolean) => {
    setIsImporting(true);
    setProgress(0);
    setErrors([]);

    try {
      // Open file dialog
      const filePath = await window.__TAURI__.dialog.open({
        multiple: false,
        filters: isZip ? [{ name: 'ZIP Files', extensions: ['zip'] }] : [{ name: 'Folders', extensions: ['*'] }],
      });

      if (filePath) {
        const result = await invoke<ImportResult>('import_from_zip', {
          inputPath: String(filePath),
          isZip,
        });

        setImportResult(result);
        setProgress(100);
      }
    } catch (error) {
      setErrors([String(error)]);
    } finally {
      setIsImporting(false);
      onComplete?.();
    }
  };

  return (
    <div className="view-container import-dashboard">
      <h2>Import Data</h2>
      
      <div className="import-options">
        <button
          className="btn btn-primary"
          onClick={() => handleImport(true)}
          disabled={isImporting}
        >
          Import from ZIP
        </button>
        
        <button
          className="btn btn-secondary"
          onClick={() => handleImport(false)}
          disabled={isImporting}
        >
          Import from Directory
        </button>
      </div>

      {isImporting && (
        <div className="import-progress">
          <div className="progress-bar">
            <div className="progress-fill" style={{ width: `${progress}%` }} />
          </div>
          <p className="progress-text">
            {currentFile || 'Processing...'} ({progress}%)
          </p>
        </div>
      )}

      {importResult && (
        <div className="import-summary">
          <h3>Import Summary</h3>
          <ul>
            <li>Messages: {importResult.messages}</li>
            <li>Conversations: {importResult.conversations}</li>
            <li>Participants: {importResult.participants}</li>
            <li>Attachments: {importResult.attachments}</li>
            <li>Duplicates removed: {importResult.duplicates}</li>
            <li>Encoding fixes: {importResult.encoding_fixes}</li>
          </ul>
        </div>
      )}

      {errors.length > 0 && (
        <div className="import-errors">
          <h3>Errors</h3>
          <ul>
            {errors.map((error, index) => (
              <li key={index}>{error}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
