CREATE TABLE IF NOT EXISTS api_logs (
  id SERIAL PRIMARY KEY,
  route TEXT NOT NULL,
  request_json JSONB,
  response_json JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);
