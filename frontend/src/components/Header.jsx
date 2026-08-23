import React from 'react';
import '../styles/Header.css';

const Header = () => {
  return (
    <header className="app-header">
      <div className="header-content">
        <div className="header-title-group">
          <div className="logo-placeholder">A&R</div>
          <div className="header-text">
            <h1>Aster & Row Policy Assistant</h1>
            <p>Evidence-grounded RAG assistant</p>
          </div>
        </div>
        <div className="header-status">
          <span className="status-dot">●</span>
          <span className="status-text" aria-label="Status: Ready">System Ready</span>
        </div>
      </div>
    </header>
  );
};

export default Header;
