"use client";

import { useState } from "react";
import { useSimulationStore } from "../store/simulationStore";

export default function EventsSheet() {
  const showEventsSheet = useSimulationStore((s) => s.showEventsSheet);
  const phase = useSimulationStore((s) => s.phase);
  const logEntries = useSimulationStore((s) => s.logEntries);
  const injectEvent = useSimulationStore((s) => s.injectEvent);
  const log = useSimulationStore((s) => s.log);

  const [eventText, setEventText] = useState("");

  const canSubmit = phase === "ready" || phase === "auto_running";

  const handleSubmit = () => {
    const prompt = eventText.trim();
    if (!prompt) return;
    if (prompt.length > 1000) {
      log("Event text too long (max 1000 chars)");
      return;
    }
    injectEvent(prompt);
    setEventText("");
  };

  return (
    <div className={`events-sheet${showEventsSheet ? " open" : ""}`}>
      <h2>Inject Event</h2>
      <div className="event-input">
        <textarea
          placeholder="Describe a city event (max 1000 chars)..."
          maxLength={1000}
          rows={3}
          value={eventText}
          onChange={(e) => setEventText(e.target.value)}
        />
        <button
          type="button"
          className="btn btn-primary"
          disabled={!canSubmit}
          onClick={handleSubmit}
        >
          Inject
        </button>
      </div>
      <div className="log">
        {logEntries.map((entry, i) => (
          <div key={i} className="log-entry">
            {entry}
          </div>
        ))}
      </div>
    </div>
  );
}
