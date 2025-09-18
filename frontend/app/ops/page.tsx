'use client';

import { FormEvent, useEffect, useMemo, useState } from 'react';
import {
  ChecklistPayload,
  ChecklistResponse,
  createChecklist,
  getOpsDashboard,
  OpsDashboard,
} from '../../lib/api';

const sedationOptions = ['IV Sedation', 'Oral Sedation', 'Local Only'];

export default function OpsCommand() {
  const [dashboard, setDashboard] = useState<OpsDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<ChecklistResponse | null>(null);

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

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    try {
      setSubmitting(true);
      setResult(null);
      setError(null);
      const checklist = await createChecklist(payload);
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
        <h2>Nuvia Ops Command Center</h2>
        <p className="form-helper">
          Track surgical volume across centers and spin up procedure-specific checklists ahead of the morning huddle.
        </p>
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

          <div className="feature-grid">
            {dashboard.locations.map((loc) => (
              <div key={loc.location} className="card">
                <h3>{loc.location}</h3>
                <p className="form-helper">Lead: {loc.team_lead}</p>
                <ul style={{ margin: 0, paddingLeft: '1.1rem', color: 'var(--text-secondary)' }}>
                  <li>{loc.surgeries_today} surgeries today</li>
                  <li>{loc.sedation_cases} sedation cases</li>
                  <li>{loc.risk_patients} risk review(s)</li>
                </ul>
                <span className="badge" style={{ marginTop: '0.8rem', width: 'fit-content' }}>
                  Status: {loc.status}
                </span>
              </div>
            ))}
          </div>

          <div className="card" style={{ display: 'grid', gap: '1.2rem' }}>
            <h3>Upcoming surgeries</h3>
            {upcomingCases.length ? (
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Patient</th>
                      <th>Procedure</th>
                      <th>Location</th>
                      <th>Surgeon</th>
                      <th>Stage</th>
                      <th>Start</th>
                    </tr>
                  </thead>
                  <tbody>
                    {upcomingCases.map((item) => (
                      <tr key={`${item.patient}-${item.start}`}>
                        <td>{item.patient}</td>
                        <td>{item.procedure}</td>
                        <td>{item.location}</td>
                        <td>{item.surgeon}</td>
                        <td>{item.stage}</td>
                        <td>{new Date(item.start).toLocaleString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
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
