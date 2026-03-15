"use client";

import { useEffect, useMemo, useRef } from "react";
import { TorontoMapboxScene } from "../world/toronto-mapbox";
import { useSimulationStore } from "../store/simulationStore";
import { buildThoughtPool } from "../utils/thoughts";

export default function MapView() {
  const containerRef = useRef<HTMLDivElement>(null);
  const sceneRef = useRef<TorontoMapboxScene | null>(null);

  const followers = useSimulationStore((s) => s.followers);
  const posts = useSimulationStore((s) => s.posts);
  const thoughtBubbleModeEnabled = useSimulationStore(
    (s) => s.thoughtBubbleModeEnabled,
  );
  const latestPost = posts[0] ?? null;

  const thoughtMessages = useMemo(() => {
    const followerNameById = new Map(
      followers.map((f) => [f.follower_id, f.name]),
    );
    return buildThoughtPool(latestPost, followerNameById);
  }, [followers, latestPost]);

  // Initialize Mapbox scene on mount, dispose on cleanup
  useEffect(() => {
    if (!containerRef.current) return;

    const scene = new TorontoMapboxScene({
      container: containerRef.current,
    });
    sceneRef.current = scene;

    const initialState = useSimulationStore.getState();
    const initialFollowerNameById = new Map(
      initialState.followers.map((f) => [f.follower_id, f.name]),
    );
    scene.setFollowers(initialState.followers);
    scene.setThoughtBubbleMessages(
      buildThoughtPool(
        initialState.posts[0] ?? null,
        initialFollowerNameById,
      ),
    );
    scene.setThoughtBubbleMode(
      initialState.thoughtBubbleModeEnabled,
    );

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
  useEffect(() => {
    sceneRef.current?.setFollowers(followers);
  }, [followers]);

  useEffect(() => {
    sceneRef.current?.setThoughtBubbleMessages(thoughtMessages);
  }, [thoughtMessages]);

  useEffect(() => {
    sceneRef.current?.setThoughtBubbleMode(thoughtBubbleModeEnabled);
  }, [thoughtBubbleModeEnabled]);

  return (
    <div
      id="canvas-container"
      ref={containerRef}
    />
  );
}
