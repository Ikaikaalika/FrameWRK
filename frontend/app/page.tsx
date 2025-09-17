export default function Home(){
  return (
    <main>
      <div className="card">
        <h1>AI App Starter</h1>
        <p>Production-grade stack with RAG, classification, summarization, and provider-agnostic LLM adapters.</p>
      </div>
      <div className="grid two">
        <a className="card" href="/chat"><h3>Chat (RAG)</h3><p>Ask questions grounded in your documents.</p></a>
        <a className="card" href="/upload"><h3>Upload</h3><p>Upload markdown to ingest into vector search.</p></a>
      </div>
      <div className="card">
        <a href="/admin"><h3>Admin</h3></a>
        <p>View recent API logs and basic metrics.</p>
      </div>
    </main>
  );
}
