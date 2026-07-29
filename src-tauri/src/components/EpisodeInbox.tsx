/**
 * EpisodeInbox component for Tauri frontend.
 * Displays detected episodes for review.
 */

import React, { useState } from 'react';

interface Episode {
  id: string;
  title: string;
  type: string;
  confidence: number;
  message_count: number;
  status: 'proposed' | 'accepted' | 'rejected';
  context: string;
}

export function EpisodeInbox() {
  const [episodes, setEpisodes] = useState<Episode[]>([]);
  const [filter, setFilter] = useState<'all' | 'proposed' | 'accepted' | 'rejected'>('all');

  const handleAccept = (id: string) => {
    setEpisodes(episodes.map(ep =>
      ep.id === id ? { ...ep, status: 'accepted' as const } : ep
    ));
  };

  const handleReject = (id: string) => {
    setEpisodes(episodes.map(ep =>
      ep.id === id ? { ...ep, status: 'rejected' as const } : ep
    ));
  };

  const filteredEpisodes = episodes.filter(ep => filter === 'all' || ep.status === filter);

  return (
    <div className="view-container episode-inbox">
      <h2>Episode Inbox</h2>

      <div className="episode-filters">
        {(['all', 'proposed', 'accepted', 'rejected'] as const).map(f => (
          <button
            key={f}
            className={`filter-btn ${filter === f ? 'active' : ''}`}
            onClick={() => setFilter(f)}
          >
            {f.charAt(0).toUpperCase() + f.slice(1)}
          </button>
        ))}
      </div>

      <div className="episode-list">
        {filteredEpisodes.map(episode => (
          <div key={episode.id} className={`episode-card ${episode.status}`}>
            <div className="episode-header">
              <h3>{episode.title}</h3>
              <span className="episode-confidence">{Math.round(episode.confidence * 100)}%</span>
            </div>
            <p className="episode-context">{episode.context}</p>
            <div className="episode-meta">
              <span className="episode-type">{episode.type}</span>
              <span>{episode.message_count} messages</span>
            </div>
            {episode.status === 'proposed' && (
              <div className="episode-actions">
                <button className="btn btn-success" onClick={() => handleAccept(episode.id)}>
                  Accept
                </button>
                <button className="btn btn-danger" onClick={() => handleReject(episode.id)}>
                  Reject
                </button>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
