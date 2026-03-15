"use client";

import { useEffect, useMemo, useState } from "react";

interface SimulationTimestampOverlayProps {
  virtualTime: string;
  sequence: number;
  durationMs?: number;
}

const TORONTO_TIME_ZONE = "America/Toronto";

function formatVirtualTime(virtualTime: string): string {
  const date = new Date(virtualTime);
  if (Number.isNaN(date.getTime())) {
    return "TIME UNAVAILABLE";
  }

  const month = new Intl.DateTimeFormat("en-US", {
    month: "short",
    timeZone: TORONTO_TIME_ZONE,
  })
    .format(date)
    .replace(/\./g, "")
    .toUpperCase();

  const day = new Intl.DateTimeFormat("en-US", {
    day: "numeric",
    timeZone: TORONTO_TIME_ZONE,
  }).format(date);

  const year = new Intl.DateTimeFormat("en-US", {
    year: "numeric",
    timeZone: TORONTO_TIME_ZONE,
  }).format(date);

  const time = new Intl.DateTimeFormat("en-US", {
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
    timeZone: TORONTO_TIME_ZONE,
  })
    .format(date)
    .replace(/\s/g, "")
    .toUpperCase();

  return `${month}. ${day}, ${year} - ${time}`;
}

export default function SimulationTimestampOverlay({
  virtualTime,
  sequence,
  durationMs = 2850,
}: SimulationTimestampOverlayProps) {
  const [visible, setVisible] = useState(false);
  const label = useMemo(
    () => formatVirtualTime(virtualTime),
    [virtualTime],
  );

  useEffect(() => {
    if (sequence < 1) return;

    setVisible(true);
    const timeoutId = window.setTimeout(() => {
      setVisible(false);
    }, durationMs);

    return () => {
      window.clearTimeout(timeoutId);
    };
  }, [durationMs, sequence]);

  if (!visible) return null;

  return (
    <div className="sim-time-flash-overlay" aria-hidden="true">
      <p className="sim-time-flash-text">{label}</p>
    </div>
  );
}
