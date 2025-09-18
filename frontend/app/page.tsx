import Link from 'next/link';

const features = [
  {
    title: 'RAG workspace',
    description: 'Ground questions in your latest runbooks with Qdrant-powered semantic search.',
    href: '/chat',
  },
  {
    title: 'One-click ingestion',
    description: 'Drop markdown playbooks or incident postmortems and watch embeddings stay in sync.',
    href: '/upload',
  },
  {
    title: 'Operational telemetry',
    description: 'Trace every LLM request in Postgres and visualize usage trends inside the Admin view.',
    href: '/admin',
  },
  {
    title: 'Provider flexibility',
    description: 'Swap between OpenAI, Anthropic, or local Ollama without touching business logic.',
    href: '/chat',
  },
];

export default function Home() {
  return (
    <section>
      <div className="hero">
        <span className="badge">Production ready AI stack</span>
        <h1>Ship incident-ready automations with confidence.</h1>
        <p>
          This hub ingests your operational knowledge, keeps the vector store fresh, and exposes reusable LLM
          utilities for classification, summarization, and retrieval-augmented chat.
        </p>
        <div className="actions">
          <Link className="btn" href="/chat">
            Open RAG chat
          </Link>
          <Link className="btn secondary" href="/upload">
            Ingest runbooks
          </Link>
        </div>
      </div>

      <div className="feature-grid">
        {features.map((feature) => (
          <Link className="card" key={feature.title} href={feature.href}>
            <h3>{feature.title}</h3>
            <p>{feature.description}</p>
          </Link>
        ))}
      </div>
    </section>
  );
}
