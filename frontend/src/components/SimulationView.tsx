"use client";

import { useEffect } from "react";
import ErrorBoundary from "./ErrorBoundary";
import HUD from "./HUD";
import MapContainer from "./MapContainer";
import Sidebar from "./Sidebar";
import EventsSheet from "./EventsSheet";
import AvatarSheet from "./AvatarSheet";
import SimulationLoadingScreen from "./SimulationLoadingScreen";
import { useKeyboardShortcuts } from "../hooks/useKeyboardShortcuts";
import { useSimulationStore } from "../store/simulationStore";

interface SimulationViewProps {
  sessionId: string;
}

export default function SimulationView({
  sessionId,
}: SimulationViewProps) {
  useKeyboardShortcuts();
  const connectToSession = useSimulationStore((s) => s.connectToSession);
  const phase = useSimulationStore((s) => s.phase);
  const connectingSessionId = useSimulationStore(
    (s) => s.connectingSessionId,
  );

  useEffect(() => {
    void connectToSession(sessionId);
  }, [connectToSession, sessionId]);
  const showWelcome = useSimulationStore((s) => s.showWelcome);

  // Cleanup on unmount: stop timers, disconnect WebSocket
  useEffect(() => {
    return () => {
      useSimulationStore.getState().disconnect();
    };
  }, []);

  const isLoading =
    phase === "loading" && connectingSessionId === sessionId;

  return (
    <ErrorBoundary>
      <MapContainer />
      {!isLoading ? (
        <>
          {!showWelcome && (
        <>
          <HUD />
              <Sidebar />
              <EventsSheet />
              <AvatarSheet />
        </>
      ) : null}
      {isLoading ? (
        <SimulationLoadingScreen
          title="Entering simulation"
          message="Initializing agents and city timeline..."
        />
      ) : null}
        </>
      )}
    </ErrorBoundary>
  );
}
