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

  // Cleanup on unmount: stop timers, disconnect WebSocket
  useEffect(() => {
    return () => {
      useSimulationStore.getState().disconnect();
    };
  }, []);

  return (
    <ErrorBoundary>
      <MapContainer />
      <HUD />
      <TweetPanel />
      <EventsSheet />
      <AvatarSheet />
    </ErrorBoundary>
  );
}
