'use client';
import { FormEvent, KeyboardEvent, useEffect, useRef, useState } from 'react';
import { ragChat } from '../../lib/api';

type Turn = { role: 'user' | 'assistant'; content: string };

const INITIAL_MESSAGE: Turn = {
  role: 'assistant',
  content: 'I’m your on-call copilot. Ask about runbooks, incidents, or write-ups and I’ll ground responses in the knowledge base.',
};

export default function Chat() {
  const [history, setHistory] = useState<Turn[]>([INITIAL_MESSAGE]);
  const [question, setQuestion] = useState(
    'What’s the recovery checklist for a failed database migration?'
  );
  const [thinking, setThinking] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const endRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [history]);

  async function sendMessage() {
    if (!question.trim()) return;
    try {
      setThinking(true);
      setError(null);
      const trimmed = question.trim();
      const userTurn: Turn = { role: 'user', content: trimmed };
      const nextHistory: Turn[] = [...history, userTurn];
      const res = await ragChat(nextHistory, trimmed);
      const assistantTurn: Turn = { role: 'assistant', content: res.answer ?? 'No answer returned.' };
      setHistory([...nextHistory, assistantTurn]);
      setQuestion('');
    } catch (err) {
      setError('Could not reach the RAG endpoint. Check the API and try again.');
      console.error(err);
    } finally {
      setThinking(false);
    }
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void sendMessage();
  }

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      void sendMessage();
    }
  }

  function clearHistory() {
    setHistory([INITIAL_MESSAGE]);
    setError(null);
  }

  return (
    <section>
      <header className="card">
        <h2>Runbook-aware chat</h2>
        <p className="form-helper">Ask operational questions, summarize incidents, or draft remediation steps.</p>
      </header>

      <div className="chat-panel">
        <div className="chat-scroll">
          {history.map((turn, index) => (
            <div key={index} className={`chat-message ${turn.role}`}>
              <span className="chat-message__role">{turn.role === 'assistant' ? 'Assistant' : 'You'}</span>
              <div className="chat-message__bubble">{turn.content}</div>
            </div>
          ))}
          <div ref={endRef} />
        </div>

        <div className="chat-toolbar">
          {error && <span className="feedback error">{error}</span>}
          <form onSubmit={handleSubmit}>
            <label className="form-helper" htmlFor="chat-input">
              Press Enter to send • Shift + Enter for a new line
            </label>
            <div className="chat-input-row">
              <textarea
                id="chat-input"
                value={question}
                placeholder="Ask how to roll back a failed deploy or summarise an incident..."
                onChange={(event) => setQuestion(event.target.value)}
                onKeyDown={handleKeyDown}
                rows={2}
              />
              <button className="btn" type="submit" disabled={thinking || !question.trim()}>
                {thinking ? 'Thinking…' : 'Send'}
              </button>
            </div>
          </form>
          <button
            className="btn secondary"
            type="button"
            onClick={clearHistory}
            disabled={history.length <= 1 || thinking}
          >
            Clear conversation
          </button>
        </div>
      </div>
    </section>
  );
}
