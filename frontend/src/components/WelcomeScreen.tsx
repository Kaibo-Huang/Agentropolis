"use client";

import { useState } from "react";
import { useSimulationStore } from "../store/simulationStore";
import StarBorderInput from "./StarBorderInput";

export default function WelcomeScreen() {
  const showWelcome = useSimulationStore((s) => s.showWelcome);
  const dismissWelcome = useSimulationStore((s) => s.dismissWelcome);
  const createAndConnect = useSimulationStore((s) => s.createAndConnect);
  const [input, setInput] = useState("");

  const handleSubmit = () => {
    if (!input.trim()) return;
    dismissWelcome();
    createAndConnect(input.trim());
  };

  return (
    <div className={`welcome-screen${showWelcome ? "" : " hidden"}`}>
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
        <StarBorderInput
          className="welcome-simulate-input"
          placeholder="What do you want to simulate?"
          aria-label="What do you want to simulate?"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onSubmit={handleSubmit}
        />
      </div>
    </div>
  );
}
