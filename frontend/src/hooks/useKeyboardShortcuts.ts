"use client";

import { useEffect } from "react";
import { useSimulationStore } from "../store/simulationStore";

export function useKeyboardShortcuts() {
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement;
      const isInput =
        target.tagName === "INPUT" || target.tagName === "TEXTAREA";

      if (e.key === " " && !e.repeat) {
        e.preventDefault();
        useSimulationStore.getState().tickOnce();
      }

      if ((e.key === "e" || e.key === "E") && !isInput) {
        e.preventDefault();
        useSimulationStore.getState().toggleEventsSheet();
      }

      if ((e.key === "a" || e.key === "A") && !isInput) {
        e.preventDefault();
        useSimulationStore.getState().toggleAvatarSheet();
      }
    };

    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, []);
}
