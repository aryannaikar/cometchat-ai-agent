import React, { useRef, useEffect } from 'react';
import { SendHorizontal } from 'lucide-react';
import '../styles/ChatInput.css';

const ChatInput = ({ value, onChange, onSubmit, disabled }) => {
  const textareaRef = useRef(null);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
    }
  }, [value]);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (!disabled && value.trim()) {
        onSubmit(e);
      }
    }
  };

  return (
    <div className="chat-input-container">
      <form onSubmit={onSubmit} className="chat-form">
        <div className="input-wrapper">
          <textarea
            ref={textareaRef}
            className="chat-textarea"
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about Aster & Row policies..."
            disabled={disabled}
            rows={1}
            aria-label="Ask about Aster & Row policies"
          />
          <button 
            type="submit" 
            className="send-button"
            disabled={disabled || !value.trim()}
            aria-label="Send message"
          >
            <SendHorizontal size={18} />
          </button>
        </div>
      </form>
      <div className="input-hint">
        Press <strong>Enter</strong> to send, <strong>Shift + Enter</strong> for a new line
      </div>
    </div>
  );
};

export default ChatInput;
