CREATE TABLE IF NOT EXISTS api_logs (
  id SERIAL PRIMARY KEY,
  route TEXT NOT NULL,
  request_json JSONB,
  response_json JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ops_generated_tasks (
  id SERIAL PRIMARY KEY,
  patient_name TEXT NOT NULL,
  task TEXT NOT NULL,
  owner TEXT NOT NULL,
  due_at TIMESTAMP,
  status TEXT DEFAULT 'pending',
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ops_automation_blueprints (
  id SERIAL PRIMARY KEY,
  title TEXT NOT NULL,
  summary TEXT,
  implementation_plan JSONB,
  status TEXT DEFAULT 'pending',
  created_at TIMESTAMP DEFAULT NOW()
);
