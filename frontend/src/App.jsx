
import { useEffect, useMemo, useState } from "react";
import "./App.css";

const API_URL = "http://localhost:5000/api/events";

function App() {
  const [events, setEvents] = useState([]);
  const [error, setError] = useState("");
  const [lastUpdated, setLastUpdated] = useState(null);

  useEffect(() => {
    let active = true;

    async function fetchEvents() {
      try {
        const response = await fetch(API_URL);

        if (!response.ok) {
          throw new Error("Unable to fetch vehicle events");
        }

        const data = await response.json();

        if (active) {
          setEvents(data);
          setError("");
          setLastUpdated(new Date());
        }
      } catch {
        if (active) {
          setError("Cannot connect to the backend. Check that it is running.");
        }
      }
    }

    fetchEvents();
    const interval = setInterval(fetchEvents, 3000);

    return () => {
      active = false;
      clearInterval(interval);
    };
  }, []);

  const colors = useMemo(() => {
    return events.reduce((result, event) => {
      const color = event.color || "Unknown";
      result[color] = (result[color] || 0) + 1;
      return result;
    }, {});
  }, [events]);

  const directions = useMemo(() => {
    return events.reduce((result, event) => {
      const direction = event.direction || "Unknown";
      result[direction] = (result[direction] || 0) + 1;
      return result;
    }, {});
  }, [events]);

  const colorStyles = {
    red: "#ef4444",
    blue: "#3b82f6",
    white: "#d1d5db",
    black: "#64748b",
    silver: "#94a3b8",
    green: "#22c55e",
    yellow: "#eab308",
  };

  function getColor(color) {
    return colorStyles[color?.toLowerCase()] || "#8b5cf6";
  }

  return (
    <main className="dashboard">
      <header className="topbar">
        <div>
          <p className="eyebrow">VISION ENGINEERING</p>
          <h1>Vehicle Analytics</h1>
          <p className="subtitle">
            Real-time vehicle monitoring dashboard
          </p>
        </div>

        <div className="connection">
          <span className={`status-dot ${error ? "offline" : ""}`} />
          {error ? "Disconnected" : "API Connected"}
        </div>
      </header>

      {error && <div className="error-banner">{error}</div>}

      <section className="metrics">
        <article className="metric-card">
          <span className="metric-icon">🚘</span>
          <p>Total recorded events</p>
          <h2>{events.length}</h2>
          <span className="metric-note">From PostgreSQL</span>
        </article>

        <article className="metric-card">
          <span className="metric-icon">🎨</span>
          <p>Colors detected</p>
          <h2>{Object.keys(colors).length}</h2>
          <span className="metric-note">Distinct color labels</span>
        </article>

        <article className="metric-card">
          <span className="metric-icon">🧭</span>
          <p>Directions</p>
          <h2>{Object.keys(directions).length}</h2>
          <span className="metric-note">Distinct directions</span>
        </article>

        <article className="metric-card">
          <span className="metric-icon">📡</span>
          <p>Latest refresh</p>
          <h2 className="refresh-value">
            {lastUpdated
              ? lastUpdated.toLocaleTimeString()
              : "Loading..."}
          </h2>
          <span className="metric-note">Refreshes every 3 seconds</span>
        </article>
      </section>

      <section className="content-grid">
        <article className="panel">
          <div className="panel-heading">
            <div>
              <h2>Vehicle colors</h2>
              <p>Breakdown by recorded color</p>
            </div>
          </div>

          {Object.entries(colors).length === 0 ? (
            <p className="empty-state">No vehicle events recorded yet.</p>
          ) : (
            <div className="breakdown">
              {Object.entries(colors)
                .sort((a, b) => b[1] - a[1])
                .map(([color, count]) => (
                  <div className="breakdown-item" key={color}>
                    <div className="breakdown-label">
                      <span
                        className="color-dot"
                        style={{ background: getColor(color) }}
                      />
                      <span>{color}</span>
                      <strong>{count}</strong>
                    </div>

                    <div className="progress-track">
                      <div
                        className="progress-fill"
                        style={{
                          width: `${(count / events.length) * 100}%`,
                          background: getColor(color),
                        }}
                      />
                    </div>
                  </div>
                ))}
            </div>
          )}
        </article>

        <article className="panel">
          <div className="panel-heading">
            <div>
              <h2>Travel directions</h2>
              <p>Recorded crossing directions</p>
            </div>
          </div>

          {Object.entries(directions).length === 0 ? (
            <p className="empty-state">No direction data available.</p>
          ) : (
            <div className="direction-list">
              {Object.entries(directions).map(([direction, count]) => (
                <div className="direction-item" key={direction}>
                  <span className="direction-arrow">↗</span>
                  <span>{direction}</span>
                  <strong>{count}</strong>
                </div>
              ))}
            </div>
          )}
        </article>
      </section>

      <section className="panel events-panel">
        <div className="panel-heading">
          <div>
            <h2>Recent vehicle events</h2>
            <p>Latest records received from the backend</p>
          </div>
          <span className="event-count">{events.length} records</span>
        </div>

        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>Event ID</th>
                <th>Vehicle ID</th>
                <th>Color</th>
                <th>Direction</th>
                <th>Source</th>
                <th>Timestamp</th>
              </tr>
            </thead>

            <tbody>
              {events.map((event) => (
                <tr key={event.id}>
                  <td>#{event.id}</td>
                  <td>
                    <strong>{event.vehicle_id}</strong>
                  </td>
                  <td>
                    <span className="color-label">
                      <span
                        className="color-dot"
                        style={{ background: getColor(event.color) }}
                      />
                      {event.color || "Unknown"}
                    </span>
                  </td>
                  <td>{event.direction || "Unknown"}</td>
                  <td>{event.source_id || "Unknown"}</td>
                  <td>
                    {event.timestamp
                      ? new Date(event.timestamp).toLocaleString()
                      : "—"}
                  </td>
                </tr>
              ))}

              {events.length === 0 && (
                <tr>
                  <td colSpan="6" className="empty-state">
                    {error
                      ? "Waiting for the backend connection..."
                      : "No vehicle events found."}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      <footer>
        Vehicle Analytics Pipeline · Development Dashboard
      </footer>
    </main>
  );
}

export default App;
