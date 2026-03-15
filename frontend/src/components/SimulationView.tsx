"use client";

import { useEffect } from "react";
import ErrorBoundary from "./ErrorBoundary";
import HUD from "./HUD";
import MapContainer from "./MapContainer";
import TweetPanel from "./TweetPanel";
import EventsSheet from "./EventsSheet";
import AvatarSheet from "./AvatarSheet";
import { useKeyboardShortcuts } from "../hooks/useKeyboardShortcuts";
import { useSimulationStore } from "../store/simulationStore";

export default function SimulationView() {
  useKeyboardShortcuts();
  const showWelcome = useSimulationStore((s) => s.showWelcome);

  // Auto-reconnect if user already dismissed welcome in a previous session
  useEffect(() => {
    const welcomed =
      typeof localStorage !== "undefined" &&
      localStorage.getItem("agentropolis_welcomed") === "true";
    if (welcomed) {
      const { dismissWelcome, createAndConnect, phase } =
        useSimulationStore.getState();
      if (phase === "idle") {
        dismissWelcome();
        createAndConnect();
      }
    }
  }, []);

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
          <TweetPanel />
          <EventsSheet />
          <AvatarSheet />
        </>
      )}
    </ErrorBoundary>
  );
}
