"use client";

import { type FormEvent, useState } from "react";
import { useSimulationStore } from "../store/simulationStore";

export default function HUD() {
  const phase = useSimulationStore((s) => s.phase);
  const session = useSimulationStore((s) => s.session);
  const followers = useSimulationStore((s) => s.followers);
  const tickOnce = useSimulationStore((s) => s.tickOnce);
  const startAutoRun = useSimulationStore((s) => s.startAutoRun);
  const stopAutoRun = useSimulationStore((s) => s.stopAutoRun);
  const injectEvent = useSimulationStore((s) => s.injectEvent);
  const toggleAvatarSheet = useSimulationStore((s) => s.toggleAvatarSheet);
  const log = useSimulationStore((s) => s.log);

  const [eventText, setEventText] = useState("");

  const canTick = phase === "ready";
  const isAutoRunning = phase === "auto_running";
  const canInject = phase === "ready" || phase === "auto_running";

  const handleInject = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!canInject) return;

    const prompt = eventText.trim();
    if (!prompt) return;
    if (prompt.length > 1000) {
      log("Event text too long (max 1000 chars)");
      return;
    }

    void injectEvent(prompt);
    setEventText("");
  };

  const dayDisplay = session
    ? new Date(session.virtual_time).toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        hour12: false,
        timeZone: "America/Toronto",
      })
    : "Loading...";

  const popDisplay = `Pop. ${followers.length > 0 ? followers.length.toLocaleString() : "--"}`;

  return (
    <header id="hud">
      <div className="hud-left">
        <h1 className="hud-title">Toronto</h1>
        <div className="hud-controls">
          <button
            type="button"
            className="btn btn-primary"
            disabled={!canTick}
            onClick={() => tickOnce()}
          >
            Tick +1h
            <span className="kbd">Space</span>
          </button>
          <button
            type="button"
            className="btn"
            disabled={phase !== "ready" && phase !== "auto_running"}
            onClick={() => (isAutoRunning ? stopAutoRun() : startAutoRun())}
          >
            {isAutoRunning ? "Stop" : "Auto-Run"}
          </button>
          <button type="button" className="btn" onClick={toggleAvatarSheet}>
            Create avatar
            <span className="kbd">A</span>
          </button>
        </div>
      </div>
      <div className="hud-center">
        <div className="time-day">{dayDisplay}</div>
        <div className="time-pop">{popDisplay}</div>
      </div>
      <div className="hud-right">
        <span className="stat-pill">
          <span className="label">Status</span>
          <span className="value">{phase === "idle" ? "Init" : phase}</span>
        </span>
      </div>
      <form className="event-bottom-form" onSubmit={handleInject}>
        <input
          id="event-prompt-input"
          className="event-bottom-input"
          type="text"
          placeholder="What do you want to simulate?"
          maxLength={1000}
          value={eventText}
          onChange={(e) => setEventText(e.target.value)}
          disabled={!canInject}
        />
        <button
          type="submit"
          className="btn btn-primary event-bottom-submit"
          disabled={!canInject || !eventText.trim()}
        >
          Inject
        </button>
      </form>
    </header>
  );
}
