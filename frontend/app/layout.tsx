import Link from 'next/link';
import './styles.css';

export const metadata = {
  title: 'AI Ops Runbook Hub',
  description: 'Incident-ready AI workspace with RAG, LLM utilities, and observability.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="bg glow" aria-hidden="true" />
        <div className="bg grid" aria-hidden="true" />
        <div className="app-shell">
          <header className="topbar">
            <Link className="brand" href="/">
              <span className="brand__dot" />
              FrameWRK Ops Hub
            </Link>
            <nav className="nav-links">
              <Link href="/">Overview</Link>
              <Link href="/chat">Chat</Link>
              <Link href="/ops">Ops Command</Link>
              <Link href="/upload">Ingest</Link>
              <Link href="/admin">Admin</Link>
            </nav>
            <a className="pill" href="https://github.com/Ikaikaalika/FrameWRK" target="_blank" rel="noreferrer">
              GitHub
            </a>
          </header>
          <main className="content">{children}</main>
          <footer className="footer">
            <span>Built to showcase production-grade AI workflows.</span>
          </footer>
        </div>
      </body>
    </html>
  );
}
