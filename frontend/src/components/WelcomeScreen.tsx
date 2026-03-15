"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useSimulationStore } from "../store/simulationStore";

export default function WelcomeScreen() {
  const router = useRouter();
  const createSession = useSimulationStore((s) => s.createSession);
  const [isStarting, setIsStarting] = useState(false);
  const [startError, setStartError] = useState<string | null>(null);

  const handleStart = async () => {
    if (isStarting) return;
    setIsStarting(true);
    setStartError(null);
    try {
      const sessionId = await createSession();
      router.push(`/sim/${sessionId}`);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to start session";
      setStartError(message);
      setIsStarting(false);
    }
  };

  return (
    <div className="welcome-screen">
      <div className="welcome-content">
        <h1 className="welcome-title">Agentropolis</h1>
        <p className="welcome-tagline">
          A living city simulation. Watch AI agents move through Toronto — run
          time, create your avatar, and inject events.
        </p>
        <ul className="welcome-features">
          <li>Moving arrows show where each agent is heading</li>
          <li>Tick or Auto-Run to advance the simulation</li>
          <li>Create your avatar and join the crowd</li>
          <li>Inject events to shape the city</li>
        </ul>
        <button
          type="button"
          className="btn btn-primary btn-welcome-start"
          disabled={isStarting}
          onClick={handleStart}
        >
          {isStarting ? "Preparing city..." : "Enter the city"}
        </button>
        {startError ? (
          <p className="welcome-error">{startError}</p>
        ) : null}
      </div>
    </div>
  );
}
