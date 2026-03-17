"use client";

import { useEffect, useRef } from "react";
import { TorontoMapboxScene } from "../world/toronto-mapbox";
import { useSimulationStore } from "../store/simulationStore";

export default function MapView() {
  const containerRef = useRef<HTMLDivElement>(null);
  const sceneRef = useRef<TorontoMapboxScene | null>(null);
  const showWelcome = useSimulationStore((s) => s.showWelcome);
  const weather = useSimulationStore((s) => s.weather);

  // Initialize Mapbox scene on mount, dispose on cleanup
  useEffect(() => {
    if (!containerRef.current) return;

    const landingFirstView = useSimulationStore.getState().showWelcome;
    const scene = new TorontoMapboxScene({
      container: containerRef.current,
      landingFirstView,
    });
    sceneRef.current = scene;

    scene.startRenderLoop(
      () => useSimulationStore.getState().hourOfDay,
    );

    return () => {
      scene.dispose();
      sceneRef.current = null;
      // Clear container for React Strict Mode double-mount
      if (containerRef.current) {
        containerRef.current.innerHTML = "";
      }
    };
  }, []);

  // Landing page: street-level route when welcome is shown, default view when dismissed
  useEffect(() => {
    if (showWelcome) {
      sceneRef.current?.startLandingRoute();
    } else {
      sceneRef.current?.stopLandingRoute();
    }
  }, [showWelcome]);

  // Sync followers from store to scene
  const followers = useSimulationStore((s) => s.followers);
  useEffect(() => {
    sceneRef.current?.setFollowers(followers);
  }, [followers]);

  // Sync weather from store to scene (snow / rain / clear)
  useEffect(() => {
    if (!sceneRef.current) return;
    sceneRef.current.setWeather(weather);
  }, [weather]);

  return (
    <div
      id="canvas-container"
      ref={containerRef}
      className={showWelcome ? "landing-active" : undefined}
    />
  );
}
