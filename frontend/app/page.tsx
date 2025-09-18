import Link from 'next/link';

const features = [
  {
    title: 'Ops command center',
    description: 'Monitor surgeries, sedation load, inventory alerts, and generate checklists in one view.',
    href: '/ops',
  },
  {
    title: 'RAG workspace',
    description: 'Ground questions in Nuvia runbooks, lab protocols, and patient communications instantly.',
    href: '/chat',
  },
  {
    title: 'One-click ingestion',
    description: 'Drop updated SOPs or consent packets to keep the knowledge base in sync.',
    href: '/upload',
  },
  {
    title: 'LLM observability',
    description: 'Audit every AI interaction with route-level metrics and JSON logs.',
    href: '/admin',
  },
];

export default function Home() {
  return (
    <section>
      <div className="hero">
        <span className="badge">Built for Nuvia Smiles operations</span>
        <h1>Coordinate dental implant surgeries with AI copilots.</h1>
        <p>
          This hub keeps surgical knowledge fresh, surfaces live metrics across centers, and delivers LLM tools to
          brief teams, triage cases, and standardize follow-up.
        </p>
        <div className="actions">
          <Link className="btn" href="/ops">
            View ops command
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
