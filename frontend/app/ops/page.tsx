'use client';

import { FormEvent, useEffect, useMemo, useState } from 'react';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';
import {
  ChecklistPayload,
  ChecklistResponse,
  createChecklist,
  getOpsDashboard,
  getGeneratedTasks,
  OpsDashboard,
  GeneratedTask,
} from '../../lib/api';

const sedationOptions = ['IV Sedation', 'Oral Sedation', 'Local Only'];

export default function OpsCommand() {
  const [dashboard, setDashboard] = useState<OpsDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<ChecklistResponse | null>(null);
  const [generatedTasks, setGeneratedTasks] = useState<GeneratedTask[]>([]);

  const [payload, setPayload] = useState<ChecklistPayload>({
    patient_name: 'Laura Ortiz',
    procedure: 'All-on-4 Upper',
    location: 'Phoenix Surgery Center',
    sedation: sedationOptions[0],
    notes: 'CBCT reviewed; ensure sedation clearance form on file.',
  });

  useEffect(() => {
    (async () => {
      try {
        setLoading(true);
        const data = await getOpsDashboard();
        setDashboard(data);
        if (data.locations.length) {
          setPayload((prev) => ({ ...prev, location: data.locations[0].location }));
        }
        const generated = await getGeneratedTasks();
        setGeneratedTasks(generated);
      } catch (err) {
        console.error(err);
        setError('Unable to load the operations dashboard.');
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const upcomingCases = useMemo(() => {
    if (!dashboard) return [];
    return dashboard.schedule.slice(0, 5);
  }, [dashboard]);

  const sedationRatio = useMemo(() => {
    if (!dashboard?.meta.total_surgeries) return 0;
    return Math.min(100, Math.round((dashboard.meta.total_sedation_cases / dashboard.meta.total_surgeries) * 100));
  }, [dashboard]);

  const highestLoad = useMemo(() => {
    if (!dashboard) return null;
    return dashboard.locations.slice().sort((a, b) => b.surgeries_today - a.surgeries_today)[0] ?? null;
  }, [dashboard]);

  const riskCenters = useMemo(() => {
    if (!dashboard) return [];
    return dashboard.locations.filter((loc) => loc.status === 'at-risk');
  }, [dashboard]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    try {
      setSubmitting(true);
      setResult(null);
      setError(null);
      const checklist = await createChecklist(payload);
      const tasks = await getGeneratedTasks();
      setGeneratedTasks(tasks);
      setResult(checklist);
    } catch (err) {
      console.error(err);
      setError('Checklist generation failed. Try again once the API is reachable.');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section>
      <header className="card">
        <div style={{ display: 'grid', gap: '0.8rem' }}>
          <span className="badge">Daily surgical readiness</span>
          <h2>Nuvia Ops Command Center</h2>
          <p className="form-helper">
            Track surgical volume across centers, watch sedation load, and spin up procedure-specific checklists ahead of the morning huddle.
          </p>
        </div>
        {highestLoad && (
          <div className="callout">
            <strong>{highestLoad.location}</strong>
            <span>
              Leading the day with {highestLoad.surgeries_today} surgeries and {highestLoad.sedation_cases} sedation cases.
              Ensure backup implant kits and anesthesia coverage are staged.
            </span>
          </div>
        )}
      </header>

      {loading ? (
        <div className="card">Loading operational data…</div>
      ) : error ? (
        <div className="card feedback error">{error}</div>
      ) : dashboard ? (
        <>
          <div className="stat-grid">
            <div className="stat">
              <span>Total surgeries today</span>
              <strong>{dashboard.meta.total_surgeries}</strong>
              <small className="form-helper">Across active centers</small>
            </div>
            <div className="stat">
              <span>Sedation cases</span>
              <strong>{dashboard.meta.total_sedation_cases}</strong>
              <small className="form-helper">Monitor anesthesia staffing</small>
            </div>
            <div className="stat">
              <span>Locations flagged</span>
              <strong>{dashboard.meta.at_risk_centers}</strong>
              <small className="form-helper">Centers tagged as at-risk</small>
            </div>
            <div className="stat">
              <span>Open ops tasks</span>
              <strong>{dashboard.meta.open_tasks}</strong>
              <small className="form-helper">Action items for today</small>
            </div>
          </div>

          <div className="metric-grid">
            <div className="metric">
              <span>Sedation load</span>
              <strong>{sedationRatio}%</strong>
              <div className="progress-track" aria-hidden>
                <div className="progress-bar" style={{ width: `${sedationRatio}%` }} />
              </div>
              <small className="form-helper">Sedation cases vs total surgeries</small>
            </div>
            <div className="metric">
              <span>At-risk centers</span>
              <strong>{riskCenters.length}</strong>
              <small className="form-helper">Needs escalation before go-live</small>
            </div>
            <div className="metric">
              <span>Checklist queue</span>
              <strong>{result ? 1 : 0}</strong>
              <small className="form-helper">Generated this session</small>
            </div>
          </div>

          <div className="card" style={{ display: 'grid', gap: '1rem' }}>
            <h3>Sedation trend (last 5 days)</h3>
            <ResponsiveContainer width="100%" height={240}>
              <AreaChart data={dashboard.sedation_trend}>
                <defs>
                  <linearGradient id="sedationColor" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#818cf8" stopOpacity={0.6} />
                    <stop offset="95%" stopColor="#818cf8" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.15)" />
                <XAxis dataKey="day" stroke="rgba(148, 163, 184, 0.6)" />
                <YAxis allowDecimals={false} stroke="rgba(148, 163, 184, 0.6)" />
                <Tooltip
                  contentStyle={{ background: 'rgba(15,23,42,0.92)', borderRadius: 12, border: '1px solid rgba(129,140,248,0.4)' }}
                />
                <Area type="monotone" dataKey="sedation_cases" stroke="#818cf8" fill="url(#sedationColor)" strokeWidth={2} />
                <Area type="monotone" dataKey="total_cases" stroke="#38bdf8" fillOpacity={0} strokeWidth={1} strokeDasharray="4 4" />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          <div className="feature-grid">
            {dashboard.locations.map((loc) => (
              <div key={loc.location} className="card">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '0.6rem' }}>
                  <div>
                    <h3>{loc.location}</h3>
                    <p className="form-helper">Lead: {loc.team_lead}</p>
                  </div>
                  <span className={`status-pill ${loc.status}`}>{loc.status}</span>
                </div>
                <div className="metric-grid" style={{ marginTop: '0.6rem' }}>
                  <div className="metric" style={{ padding: '0.6rem 0.8rem' }}>
                    <span>Surgeries</span>
                    <strong>{loc.surgeries_today}</strong>
                  </div>
                  <div className="metric" style={{ padding: '0.6rem 0.8rem' }}>
                    <span>Sedation</span>
                    <strong>{loc.sedation_cases}</strong>
                  </div>
                  <div className="metric" style={{ padding: '0.6rem 0.8rem' }}>
                    <span>Risk pts</span>
                    <strong>{loc.risk_patients}</strong>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="card" style={{ display: 'grid', gap: '1.2rem' }}>
            <h3>Upcoming surgeries</h3>
            {upcomingCases.length ? (
              <div className="timeline">
                {upcomingCases.map((item) => (
                  <div key={`${item.patient}-${item.start}`} className="timeline-item">
                    <strong>{item.patient} — {item.procedure}</strong>
                    <div className="form-helper">
                      {new Date(item.start).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} • {item.location}
                    </div>
                    <div className="form-helper">Surgeon: {item.surgeon} • Stage: {item.stage}</div>
                    <div className="form-helper">Notes: {item.notes}</div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="empty-state">No scheduled cases in the data set.</div>
            )}
          </div>

          <div className="feature-grid">
            <div className="card" style={{ display: 'grid', gap: '1rem' }}>
              <h3>Priority tasks</h3>
              {dashboard.tasks.map((task) => (
                <div key={`${task.title}-${task.owner}`} className="chat-message__bubble" style={{ background: 'rgba(15,23,42,0.75)' }}>
                  <strong>{task.title}</strong>
                  <div className="form-helper">Owner: {task.owner}</div>
                  <div className="form-helper">Due: {new Date(task.due).toLocaleTimeString()}</div>
                  <div className="form-helper">Priority: {task.priority}</div>
                </div>
              ))}
            </div>

            <div className="card" style={{ display: 'grid', gap: '1rem' }}>
              <h3>Inventory alerts</h3>
              {dashboard.inventory_alerts.map((alert) => (
                <div
                  key={`${alert.item}-${alert.location}`}
                  className="chat-message__bubble"
                  style={{ background: 'rgba(79,70,229,0.12)', borderColor: 'rgba(129,140,248,0.4)' }}
                >
                  <strong>{alert.item}</strong>
                  <div className="form-helper">Location: {alert.location}</div>
                  <div className="form-helper">Status: {alert.status}</div>
                  <div className="form-helper">On-hand: {alert.on_hand} • Par: {alert.par_level}</div>
                </div>
              ))}
            </div>

            <div className="card" style={{ display: 'grid', gap: '1rem' }}>
              <h3>Follow-up queue</h3>
              {dashboard.followups.map((item) => (
                <div key={`${item.patient}-${item.type}`} className="chat-message__bubble">
                  <strong>{item.patient}</strong>
                  <div className="form-helper">Type: {item.type}</div>
                  <div className="form-helper">Due: {new Date(item.due).toLocaleString()}</div>
                  <div className="form-helper">Status: {item.status}</div>
                </div>
              ))}
            </div>

            <div className="card" style={{ display: 'grid', gap: '1rem' }}>
              <h3>Generated tasks</h3>
              {generatedTasks.length ? (
                generatedTasks.slice(0, 5).map((task) => (
                  <div key={task.id} className="chat-message__bubble" style={{ background: 'rgba(17,24,39,0.9)' }}>
                    <strong>{task.task}</strong>
                    <div className="form-helper">Patient: {task.patient_name}</div>
                    <div className="form-helper">Owner: {task.owner}</div>
                    <div className="form-helper">Due: {task.due_at ? new Date(task.due_at).toLocaleString() : 'TBD'}</div>
                    <div className="form-helper">Status: {task.status}</div>
                  </div>
                ))
              ) : (
                <div className="empty-state">Generated tasks will appear here after checklist runs.</div>
              )}
            </div>

            <div className="card" style={{ display: 'grid', gap: '1.2rem' }}>
              <h3>Generate pre-op checklist</h3>
              <form onSubmit={handleSubmit} className="chat-toolbar">
                <label className="form-helper" htmlFor="patient_name">Patient name</label>
                <input
                  id="patient_name"
                  value={payload.patient_name}
                  onChange={(event) => setPayload({ ...payload, patient_name: event.target.value })}
                  required
                />

                <label className="form-helper" htmlFor="procedure">Procedure</label>
                <input
                  id="procedure"
                  value={payload.procedure}
                  onChange={(event) => setPayload({ ...payload, procedure: event.target.value })}
                  required
                />

                <label className="form-helper" htmlFor="location">Location</label>
                <select
                  id="location"
                  value={payload.location}
                  onChange={(event) => setPayload({ ...payload, location: event.target.value })}
                >
                  {dashboard.locations.map((loc) => (
                    <option key={loc.location} value={loc.location}>
                      {loc.location}
                    </option>
                  ))}
                </select>

                <label className="form-helper" htmlFor="sedation">Sedation plan</label>
                <select
                  id="sedation"
                  value={payload.sedation}
                  onChange={(event) => setPayload({ ...payload, sedation: event.target.value })}
                >
                  {sedationOptions.map((option) => (
                    <option key={option} value={option}>
                      {option}
                    </option>
                  ))}
                </select>

                <label className="form-helper" htmlFor="notes">Notes</label>
                <textarea
                  id="notes"
                  rows={3}
                  value={payload.notes ?? ''}
                  onChange={(event) => setPayload({ ...payload, notes: event.target.value })}
                />

                <button className="btn" type="submit" disabled={submitting}>
                  {submitting ? 'Generating…' : 'Generate checklist'}
                </button>
              </form>

              {result && (
                <div className="chat-message__bubble" style={{ background: 'rgba(15,23,42,0.85)' }}>
                  <strong>{result.title}</strong>
                  <ul style={{ margin: '0.75rem 0', paddingLeft: '1.1rem' }}>
                    {result.checklist.map((item, index) => (
                      <li key={index}>{item}</li>
                    ))}
                  </ul>
                  <strong>Follow-up</strong>
                  <ul style={{ margin: '0.5rem 0 0', paddingLeft: '1.1rem' }}>
                    {result.follow_up.map((item, index) => (
                      <li key={index}>{item}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        </>
      ) : null}
    </section>
  );
}
