import React, { useState } from 'react';
import { User, ShieldAlert, AlertTriangle, XCircle, CheckCircle2, FileText, ChevronDown, ChevronUp, ShieldCheck } from 'lucide-react';
import '../styles/MessageBubble.css';

const MessageBubble = ({ message }) => {
  const isUser = message.type === 'user';
  const [verificationExpanded, setVerificationExpanded] = useState(false);

  if (isUser) {
    return (
      <div className="message-row user-row">
        <div className="message-content user-content">
          <p>{message.text}</p>
        </div>
        <div className="avatar-wrapper user-avatar">
          <User size={18} />
        </div>
      </div>
    );
  }

  const { data } = message;
  const decision = data?.decision?.toLowerCase();

  // Decision Header Banners according to spec
  const renderDecisionBanner = () => {
    switch (decision) {
      case 'abstain':
        return (
          <div className="decision-banner abstain">
            <AlertTriangle size={16} />
            <span>Not enough reliable evidence</span>
          </div>
        );
      case 'human_handoff':
        return (
          <div className="decision-banner handoff">
            <ShieldAlert size={16} />
            <span>Authoritative policy evidence conflicts. Human review required.</span>
          </div>
        );
      case 'reject':
        return (
          <div className="decision-banner reject">
            <XCircle size={16} />
            <span>Request Validation / Safety Gate Triggered</span>
          </div>
        );
      case 'answer':
      default:
        return (
          <div className="verification-summary-banner">
            <CheckCircle2 size={15} className="verified-icon" />
            <span>Answer verified against policy evidence</span>
          </div>
        );
    }
  };

  return (
    <div className="message-row bot-row">
      <div className="avatar-wrapper bot-avatar">
        A&R
      </div>
      <div className="message-content bot-content">
        {renderDecisionBanner()}
        
        <div className="answer-text">
          {data.answer}
        </div>

        {/* Polished Citations / Sources */}
        {data.citations && data.citations.length > 0 && (
          <div className="sources-section">
            <div className="sources-header">
              <FileText size={14} />
              <span>Sources · {data.citations.length}</span>
            </div>
            <div className="sources-list">
              {data.citations.map((cite, idx) => {
                const parts = cite.split(' — ');
                const fileName = parts[0];
                const sourceTag = parts[1] || 'Knowledge base';
                return (
                  <div key={idx} className="source-card">
                    <span className="source-icon">📄</span>
                    <div className="source-info">
                      <span className="source-name">{fileName}</span>
                      <span className="source-tag">{sourceTag}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Collapsible Verification Details */}
        <div className="verification-details-container">
          <button 
            className="verification-toggle-btn"
            onClick={() => setVerificationExpanded(!verificationExpanded)}
            aria-expanded={verificationExpanded}
          >
            <ShieldCheck size={14} />
            <span>Verification details</span>
            {verificationExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          </button>
          
          {verificationExpanded && (
            <div className="verification-details-body">
              <div className="verification-row">
                <span className="v-label">Decision</span>
                <span className={`v-value ${decision}`}>{data.decision?.toUpperCase() || 'UNKNOWN'}</span>
              </div>
              {data.input_guard_decision && (
                <div className="verification-row">
                  <span className="v-label">Input Guard</span>
                  <span className={`v-value ${data.input_guard_decision.toLowerCase()}`}>{data.input_guard_decision.toUpperCase()}</span>
                </div>
              )}
              {data.evidence_guard_decision && (
                <div className="verification-row">
                  <span className="v-label">Evidence Guard</span>
                  <span className={`v-value ${data.evidence_guard_decision.toLowerCase()}`}>{data.evidence_guard_decision.toUpperCase()}</span>
                </div>
              )}
              {data.output_guard_decision && (
                <div className="verification-row">
                  <span className="v-label">Output Guard</span>
                  <span className={`v-value ${data.output_guard_decision.toLowerCase()}`}>{data.output_guard_decision.toUpperCase()}</span>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default MessageBubble;
