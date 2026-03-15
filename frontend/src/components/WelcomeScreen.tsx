"use client";

import { useSimulationStore } from "../store/simulationStore";

export default function WelcomeScreen() {
  const showWelcome = useSimulationStore((s) => s.showWelcome);
  const dismissWelcome = useSimulationStore((s) => s.dismissWelcome);
  const createAndConnect = useSimulationStore((s) => s.createAndConnect);

  const handleStart = () => {
    dismissWelcome();
    createAndConnect();
  };

  return (
    <div className={`welcome-screen${showWelcome ? "" : " hidden"}`}>
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
          onClick={handleStart}
        >
          Enter the city
        </button>
      </div>
    </div>
  );
}
