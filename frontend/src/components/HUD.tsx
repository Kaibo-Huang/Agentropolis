"use client";

import { useSimulationStore } from "../store/simulationStore";

export default function HUD() {
  const phase = useSimulationStore((s) => s.phase);
  const session = useSimulationStore((s) => s.session);
  const followers = useSimulationStore((s) => s.followers);
  const tickOnce = useSimulationStore((s) => s.tickOnce);
  const startAutoRun = useSimulationStore((s) => s.startAutoRun);
  const stopAutoRun = useSimulationStore((s) => s.stopAutoRun);
  const toggleEventsSheet = useSimulationStore((s) => s.toggleEventsSheet);
  const toggleAvatarSheet = useSimulationStore((s) => s.toggleAvatarSheet);

  const canTick = phase === "ready";
  const isAutoRunning = phase === "auto_running";

  const dayDisplay = session
    ? new Date(session.virtual_time).toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        hour12: false,
        timeZone: "UTC",
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
          <button type="button" className="btn" onClick={toggleEventsSheet}>
            Events
            <span className="kbd">E</span>
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
    </header>
  );
}
