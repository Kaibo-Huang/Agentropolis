"use client";

import { useEffect, useRef, useState } from "react";
import ErrorBoundary from "./ErrorBoundary";
import HUD from "./HUD";
import MapContainer from "./MapContainer";
import Sidebar from "./Sidebar";
import AvatarSheet from "./AvatarSheet";
import SimulationLoadingScreen from "./SimulationLoadingScreen";
import SimulationTimestampOverlay from "./SimulationTimestampOverlay";
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
  const session = useSimulationStore((s) => s.session);
  const [timeOverlaySequence, setTimeOverlaySequence] =
    useState(0);
  const sawLoadingRef = useRef(false);
  const overlayDelayTimeoutRef =
    useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    void connectToSession(sessionId);
  }, [connectToSession, sessionId]);
  const showWelcome = useSimulationStore((s) => s.showWelcome);

  // Cleanup on unmount: stop timers, disconnect WebSocket
  useEffect(() => {
    return () => {
      if (overlayDelayTimeoutRef.current !== null) {
        clearTimeout(overlayDelayTimeoutRef.current);
        overlayDelayTimeoutRef.current = null;
      }
      useSimulationStore.getState().disconnect();
    };
  }, []);

  const isLoading =
    phase === "loading" && connectingSessionId === sessionId;
  const loadedSessionId = session?.session_id ?? null;
  const virtualTime = session?.virtual_time ?? null;

  useEffect(() => {
    if (isLoading) {
      if (overlayDelayTimeoutRef.current !== null) {
        clearTimeout(overlayDelayTimeoutRef.current);
        overlayDelayTimeoutRef.current = null;
      }
      sawLoadingRef.current = true;
      return;
    }

    if (!sawLoadingRef.current) return;
    if (!virtualTime || loadedSessionId !== sessionId) return;

    sawLoadingRef.current = false;
    overlayDelayTimeoutRef.current = setTimeout(() => {
      setTimeOverlaySequence((current) => current + 1);
      overlayDelayTimeoutRef.current = null;
    }, 1000);

    return () => {
      if (overlayDelayTimeoutRef.current !== null) {
        clearTimeout(overlayDelayTimeoutRef.current);
        overlayDelayTimeoutRef.current = null;
      }
    };
  }, [isLoading, loadedSessionId, sessionId, virtualTime]);

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
      {virtualTime ? (
        <SimulationTimestampOverlay
          virtualTime={virtualTime}
          sequence={timeOverlaySequence}
        />
      ) : null}
    </ErrorBoundary>
  );
}
