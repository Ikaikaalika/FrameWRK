'use client';
import { DragEvent, useState } from 'react';
import { ingestDocs } from '../../lib/api';

export default function Upload() {
  const [files, setFiles] = useState<File[]>([]);
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  function handleFiles(list: FileList | null) {
    if (!list) return;
    const allowedExtensions = ['.md', '.txt', '.json'];
    const supported = Array.from(list).filter((file) =>
      allowedExtensions.some((ext) => file.name.toLowerCase().endsWith(ext)) ||
      ['text/markdown', 'text/plain', 'application/json'].includes(file.type)
    );
    if (!supported.length) {
      setError('Please upload .md, .txt, or .json files.');
      return;
    }
    setFiles(supported);
    setStatus(null);
    setError(null);
  }

  async function handleIngest() {
    if (!files.length) {
      setError('Select at least one supported file (.md, .txt, .json) to ingest.');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const texts = await Promise.all(files.map((file) => file.text()));
      const res = await ingestDocs(texts);
      const ingested = res.ingested ?? texts.length;
      setStatus(`Ingested ${ingested} document${ingested === 1 ? '' : 's'}.`);
    } catch (err) {
      console.error(err);
      setError('Failed to ingest documents — ensure the backend is running.');
    } finally {
      setLoading(false);
    }
  }

  function onDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    handleFiles(event.dataTransfer.files);
  }

  return (
    <section>
      <header className="card">
        <h2>Upload & ingest runbooks</h2>
        <p className="form-helper">Drop markdown, plain-text, or JSON notes to keep the vector store synced with your latest playbooks.</p>
      </header>

      <div className="card" style={{ gap: '1.4rem' }}>
        <div
          className="upload-dropzone"
          onDragOver={(event) => event.preventDefault()}
          onDrop={onDrop}
        >
          <strong>Drag & drop .md / .txt / .json files</strong>
          <span className="form-helper">or</span>
          <label className="btn secondary" htmlFor="file-input" role="button" tabIndex={0}>
            Browse files
          </label>
          <input
            id="file-input"
            type="file"
            accept=".md,.txt,.json,text/markdown,text/plain,application/json"
            multiple
            style={{ display: 'none' }}
            onChange={(event) => handleFiles(event.target.files)}
          />
        </div>

        {files.length > 0 ? (
          <div className="file-list">
            {files.map((file) => (
              <span key={file.name} className="file-pill">
                {file.name}
              </span>
            ))}
          </div>
        ) : (
          <div className="empty-state">No files selected yet.</div>
        )}

        {status && <span className="feedback success">{status}</span>}
        {error && <span className="feedback error">{error}</span>}

        <div className="actions">
          <button className="btn" type="button" onClick={handleIngest} disabled={loading || !files.length}>
            {loading ? 'Ingesting…' : 'Ingest documents'}
          </button>
          <button
            className="btn secondary"
            type="button"
            onClick={() => {
              setFiles([]);
              setStatus(null);
              setError(null);
            }}
          >
            Clear selection
          </button>
        </div>
      </div>
    </section>
  );
}
