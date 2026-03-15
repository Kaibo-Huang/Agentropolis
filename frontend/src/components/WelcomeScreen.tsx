"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useSimulationStore } from "../store/simulationStore";
import StarBorderInput from "./StarBorderInput";

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
  }
  
  const handleSubmit = () => {
    dismissWelcome();
    createAndConnect();
  };

  return (
    <div className="welcome-screen">
      <div className="welcome-content">
        <img
          src="/logo.svg"
          alt="Agentropolis"
          className="welcome-logo"
        />
        <p className="welcome-tagline">
        A living city simulation.<br></br>
        Watch thousands of AI agents move through Toronto in real time.
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
        <StarBorderInput
          className="welcome-simulate-input"
          placeholder="What do you want to simulate?"
          aria-label="What do you want to simulate?"
          onSubmit={handleSubmit}
        />
      </div>
    </div>
  );
}
