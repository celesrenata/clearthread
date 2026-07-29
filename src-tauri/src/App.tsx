import React, { useState } from 'react';
import { ImportDashboard } from './components/ImportDashboard';
import { RelationshipLibrary } from './components/RelationshipLibrary';
import { TimelineView } from './components/TimelineView';
import { EpisodeInbox } from './components/EpisodeInbox';
import { PatternFindings } from './components/PatternFindings';
import { TherapyBriefBuilder } from './components/TherapyBriefBuilder';
import { GrowthView } from './components/GrowthView';
import { EvidenceReader } from './components/EvidenceReader';
import { ExportCenter } from './components/ExportCenter';
import { SettingsPanel } from './components/SettingsPanel';

type ViewType =
  | 'import'
  | 'library'
  | 'timeline'
  | 'episodes'
  | 'patterns'
  | 'brief'
  | 'growth'
  | 'evidence'
  | 'export'
  | 'settings';

export default function App() {
  const [currentView, setCurrentView] = useState<ViewType>('library');
  const [isDark, setIsDark] = useState(false);

  const renderView = () => {
    switch (currentView) {
      case 'import':
        return <ImportDashboard onComplete={() => setCurrentView('library')} />;
      case 'library':
        return <RelationshipLibrary />;
      case 'timeline':
        return <TimelineView />;
      case 'episodes':
        return <EpisodeInbox />;
      case 'patterns':
        return <PatternFindings />;
      case 'brief':
        return <TherapyBriefBuilder />;
      case 'growth':
        return <GrowthView />;
      case 'evidence':
        return <EvidenceReader />;
      case 'export':
        return <ExportCenter />;
      case 'settings':
        return <SettingsPanel />;
      default:
        return <RelationshipLibrary />;
    }
  };

  return (
    <div className={`app ${isDark ? 'dark' : 'light'}`}>
      <nav className="sidebar">
        <div className="sidebar-header">
          <h1>ClearThread</h1>
        </div>
        <ul className="sidebar-nav">
          <li onClick={() => setCurrentView('import')}>Import</li>
          <li onClick={() => setCurrentView('library')}>Library</li>
          <li onClick={() => setCurrentView('timeline')}>Timeline</li>
          <li onClick={() => setCurrentView('episodes')}>Episodes</li>
          <li onClick={() => setCurrentView('patterns')}>Patterns</li>
          <li onClick={() => setCurrentView('growth')}>Growth</li>
          <li onClick={() => setCurrentView('brief')}>Brief Builder</li>
          <li onClick={() => setCurrentView('evidence')}>Evidence</li>
          <li onClick={() => setCurrentView('export')}>Export</li>
          <li onClick={() => setCurrentView('settings')}>Settings</li>
        </ul>
        <div className="sidebar-footer">
          <button onClick={() => setIsDark(!isDark)}>
            {isDark ? 'Light Mode' : 'Dark Mode'}
          </button>
        </div>
      </nav>
      <main className="main-content">
        {renderView()}
      </main>
    </div>
  );
}
