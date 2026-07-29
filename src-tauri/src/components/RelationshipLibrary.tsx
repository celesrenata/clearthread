/**
 * RelationshipLibrary component for Tauri frontend.
 * Displays all conversations and participants.
 */

import React, { useState, useEffect } from 'react';
import { invoke } from '@tauri-apps/api/core';

export function RelationshipLibrary() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [participants, setParticipants] = useState<Participant[]>([]);
  const [selectedConversation, setSelectedConversation] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  interface Conversation {
    id: string;
    name: string;
    message_count: number;
    last_message: string;
  }

  interface Participant {
    id: string;
    name: string;
    message_count: number;
    relationship_category: string;
  }

  useEffect(() => {
    loadLibrary();
  }, []);

  const loadLibrary = async () => {
    setIsLoading(true);
    try {
      // In production, these would call Rust commands
      const [convResponse, partResponse] = await Promise.all([
        invoke<Conversation[]>('get_conversations'),
        invoke<Participant[]>('get_participants'),
      ]);

      setConversations(convResponse);
      setParticipants(partResponse);
    } catch (error) {
      console.error('Failed to load library:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="view-container library">
      <h2>Relationship Library</h2>
      
      <div className="library-layout">
        <aside className="conversation-list">
          <h3>Conversations</h3>
          <ul>
            {conversations.map((conv) => (
              <li
                key={conv.id}
                className={selectedConversation === conv.id ? 'active' : ''}
                onClick={() => setSelectedConversation(conv.id)}
              >
                <span className="conv-name">{conv.name}</span>
                <span className="conv-count">{conv.message_count} messages</span>
              </li>
            ))}
          </ul>
        </aside>

        <main className="participant-grid">
          <h3>Participants</h3>
          <div className="grid">
            {participants.map((participant) => (
              <div key={participant.id} className="participant-card">
                <div className="participant-avatar">
                  {participant.name.charAt(0).toUpperCase()}
                </div>
                <div className="participant-info">
                  <span className="participant-name">{participant.name}</span>
                  <span className="participant-category">{participant.relationship_category}</span>
                </div>
              </div>
            ))}
          </div>
        </main>
      </div>

      {isLoading && <div className="loading">Loading...</div>}
    </div>
  );
}
