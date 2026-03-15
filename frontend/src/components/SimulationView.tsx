"use client";

import { useEffect } from "react";
import ErrorBoundary from "./ErrorBoundary";
import HUD from "./HUD";
import MapContainer from "./MapContainer";
import Toolkit from "./Toolkit";
import { useSimulationStore } from "../store/simulationStore";

export default function SimulationView() {
  const showWelcome = useSimulationStore((s) => s.showWelcome);

  // Cleanup on unmount: stop timers, disconnect WebSocket
  useEffect(() => {
    return () => {
      useSimulationStore.getState().disconnect();
    };
  }, []);

  return (
    <ErrorBoundary>
      <MapContainer />
      {!showWelcome && (
        <>
          <HUD />
          <Toolkit />
        </>
      )}
    </ErrorBoundary>
  );
}
