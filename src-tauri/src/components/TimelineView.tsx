/**
 * TimelineView component for Tauri frontend.
 * Displays messages chronologically.
 */

import React, { useState, useEffect, useRef } from 'react';

export function TimelineView() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [dateRange, setDateRange] = useState<{ start: string; end: string }>({
    start: '',
    end: '',
  });
  const scrollRef = useRef<HTMLDivElement>(null);

  interface Message {
    id: string;
    sender: string;
    text: string;
    timestamp: string;
    is_own: boolean;
    attachments: string[];
  }

  useEffect(() => {
    loadTimeline();
  }, []);

  const loadTimeline = async () => {
    setIsLoading(true);
    // In production, fetch from Rust/Python backend
    setMessages([]);
    setIsLoading(false);
  };

  return (
    <div className="view-container timeline">
      <div className="timeline-header">
        <h2>Timeline</h2>
        <div className="date-range">
          <input
            type="date"
            value={dateRange.start}
            onChange={(e) => setDateRange({ ...dateRange, start: e.target.value })}
          />
          <span>to</span>
          <input
            type="date"
            value={dateRange.end}
            onChange={(e) => setDateRange({ ...dateRange, end: e.target.value })}
          />
        </div>
      </div>

      <div className="timeline-content" ref={scrollRef}>
        {isLoading ? (
          <div className="loading">Loading timeline...</div>
        ) : (
          <div className="messages">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`message ${msg.is_own ? 'own' : 'other'}`}
              >
                <div className="message-sender">{msg.sender}</div>
                <div className="message-text">{msg.text}</div>
                <div className="message-time">{msg.timestamp}</div>
                {msg.attachments.length > 0 && (
                  <div className="message-attachments">
                    {msg.attachments.map((att, i) => (
                      <img key={i} src={att} alt="attachment" className="attachment" />
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
