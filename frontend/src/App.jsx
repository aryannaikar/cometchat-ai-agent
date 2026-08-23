import React, { useState } from 'react';
import Header from './components/Header';
import EmptyState from './components/EmptyState';
import ChatWindow from './components/ChatWindow';
import ChatInput from './components/ChatInput';
import { queryAssistant } from './services/api';
import './App.css';

function App() {
  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleAskQuestion = async (text) => {
    if (!text.trim() || loading) return;

    const userMessage = { type: "user", text: text };
    setMessages((prev) => [...prev, userMessage]);
    setQuestion("");
    setLoading(true);
    setError(null);

    try {
      const historyForApi = messages.map(m => ({
        type: m.type,
        text: m.type === 'user' ? m.text : (m.data?.answer || "")
      }));
      
      const data = await queryAssistant(userMessage.text, historyForApi);
      const botMessage = { type: "bot", data };
      setMessages((prev) => [...prev, botMessage]);
    } catch (err) {
      setError(err.message || "An unexpected error occurred while communicating with the assistant.");
      
      // Add a fallback bot message to show the error in the chat
      setMessages((prev) => [...prev, {
        type: "bot",
        data: {
          decision: "reject",
          answer: err.message || "An unexpected error occurred. Please make sure the backend is running.",
          citations: []
        }
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    handleAskQuestion(question);
  };

  return (
    <div className="app-layout">
      <Header />
      
      <main className="main-content">
        {messages.length === 0 ? (
          <EmptyState onExampleClick={(q) => handleAskQuestion(q)} />
        ) : (
          <ChatWindow messages={messages} loading={loading} />
        )}
      </main>

      <ChatInput 
        value={question}
        onChange={setQuestion}
        onSubmit={handleSubmit}
        disabled={loading}
      />
    </div>
  );
}

export default App;
