import React from 'react';
import { BookOpen } from 'lucide-react';
import '../styles/EmptyState.css';

const EmptyState = ({ onExampleClick }) => {
  const topics = [
    "Returns & Return Windows",
    "Damaged or Defective Items",
    "Final-Sale Items & Promotions",
    "Gift Cards & Refundability",
    "Membership Policies (TrailPlus)"
  ];

  const examples = [
    "Can I return my shoes after 20 days?",
    "Can I return my shoes after 40 days?",
    "What is the standard return window?",
    "What happens if my item is defective?"
  ];

  return (
    <div className="empty-state-container">
      <div className="welcome-card">
        <div className="icon-wrapper">
          <BookOpen size={28} className="welcome-icon" />
        </div>
        <h2>Aster & Row Policy Assistant</h2>
        <p className="welcome-text">
          Ask questions about Aster & Row official policies. All answers are grounded in the verified policy knowledge base.
        </p>

        <div className="topics-box">
          <span className="topics-title">Ask questions about:</span>
          <ul className="topics-list">
            {topics.map((topic, idx) => (
              <li key={idx}>• {topic}</li>
            ))}
          </ul>
        </div>

        <div className="examples-section">
          <h3>Example questions:</h3>
          <div className="examples-grid">
            {examples.map((example, idx) => (
              <button 
                key={idx} 
                className="example-btn"
                onClick={() => onExampleClick(example)}
                aria-label={`Ask: ${example}`}
              >
                {example}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default EmptyState;
