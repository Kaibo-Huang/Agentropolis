"use client";

import { useEffect, useRef } from "react";
import { TorontoMapboxScene } from "../world/toronto-mapbox";
import { useSimulationStore } from "../store/simulationStore";

export default function MapView() {
  const containerRef = useRef<HTMLDivElement>(null);
  const sceneRef = useRef<TorontoMapboxScene | null>(null);

  // Initialize Mapbox scene on mount, dispose on cleanup
  useEffect(() => {
    if (!containerRef.current) return;

    const scene = new TorontoMapboxScene({ container: containerRef.current });
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

  // Sync followers from store to scene
  const followers = useSimulationStore((s) => s.followers);
  useEffect(() => {
    sceneRef.current?.setFollowers(followers);
  }, [followers]);

  return <div id="canvas-container" ref={containerRef} />;
}
