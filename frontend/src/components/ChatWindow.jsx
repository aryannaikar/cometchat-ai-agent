import React, { useEffect, useRef } from 'react';
import MessageBubble from './MessageBubble';
import '../styles/ChatWindow.css';

const ChatWindow = ({ messages, loading }) => {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  return (
    <div className="chat-window">
      <div className="messages-container">
        {messages.map((msg, idx) => (
          <MessageBubble key={idx} message={msg} />
        ))}
        
        {loading && (
          <div className="message-row bot-row">
            <div className="avatar-wrapper bot-avatar">A&R</div>
            <div className="message-content bot-content loading-content">
              <div className="typing-indicator">
                <span>●</span>
                <span>●</span>
                <span>●</span>
              </div>
              <span className="loading-text">Analyzing policy evidence...</span>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  );
};

export default ChatWindow;
