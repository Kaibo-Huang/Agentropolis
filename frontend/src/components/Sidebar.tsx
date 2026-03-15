"use client";

import { useEffect, useMemo, useState } from "react";
import TweetPanel from "./TweetPanel";
import { useSimulationStore } from "../store/simulationStore";

const THOUGHT_ROTATION_MS = 7000;

const BASE_AGENT_THOUGHTS = [
  "Transit nodes are busier than usual. Small delay, big ripple.",
  "A quiet morning often becomes an active afternoon.",
  "Happiness drifts upward when routes stay predictable.",
  "Neighborhood chatter tends to spike right after each tick.",
  "Agents near the core react faster to event changes.",
];

type SidebarSectionId = "clock" | "thoughts" | "posts";

const SECTIONS: Array<{
  id: SidebarSectionId;
  label: string;
}> = [
  { id: "clock", label: "Clock" },
  { id: "thoughts", label: "Thoughts" },
  { id: "posts", label: "Posts" },
];

function SidebarTabIcon({
  sectionId,
}: {
  sectionId: SidebarSectionId;
}) {
  if (sectionId === "clock") {
    return (
      <svg
        className="sidebar-tab-icon"
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        <circle cx="12" cy="12" r="8" />
        <path d="M12 8.5V12.5L14.8 14.3" />
      </svg>
    );
  }

  if (sectionId === "thoughts") {
    return (
      <svg
        className="sidebar-tab-icon"
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        <path d="M6 8.5a6 6 0 0 1 12 0c0 2-1.1 3.2-2.4 4.1-.9.6-1.5 1.4-1.6 2.4H9.9c-.1-1-0.7-1.8-1.6-2.4C7.1 11.7 6 10.5 6 8.5Z" />
        <path d="M10 17.5h4" />
        <path d="M10.5 20h3" />
      </svg>
    );
  }

  return (
    <svg
      className="sidebar-tab-icon"
      viewBox="0 0 24 24"
      aria-hidden="true"
    >
      <rect x="5.5" y="5.5" width="13" height="13" rx="2.5" />
      <path d="M8.5 9.5h7" />
      <path d="M8.5 12h7" />
      <path d="M8.5 14.5h4.8" />
    </svg>
  );
}

function pickDifferentIndex(length: number, current: number): number {
  if (length <= 1) return 0;
  let next = current;
  while (next === current) {
    next = Math.floor(Math.random() * length);
  }
  return next;
}

export default function Sidebar() {
  const posts = useSimulationStore((s) => s.posts);
  const followers = useSimulationStore((s) => s.followers);
  const phase = useSimulationStore((s) => s.phase);
  const latestPost = posts[0] ?? null;

  const [activeSection, setActiveSection] =
    useState<SidebarSectionId | null>(null);
  const [now, setNow] = useState<Date | null>(null);
  const [thoughtIndex, setThoughtIndex] = useState(0);

  const followerNameById = useMemo(
    () => new Map(followers.map((f) => [f.follower_id, f.name])),
    [followers],
  );

  const thoughts = useMemo(() => {
    const pool = [...BASE_AGENT_THOUGHTS];
    if (latestPost) {
      const snippet =
        latestPost.text.length > 68
          ? `${latestPost.text.slice(0, 65)}...`
          : latestPost.text;
      const author =
        followerNameById.get(latestPost.follower_id) ??
        `Follower #${latestPost.follower_id}`;
      pool.unshift(`${author}: ${snippet}`);
    }
    return pool;
  }, [latestPost, followerNameById]);

  useEffect(() => {
    setThoughtIndex(Math.floor(Math.random() * thoughts.length));
  }, [thoughts.length]);

  useEffect(() => {
    setNow(new Date());
    const clockTimer = window.setInterval(() => {
      setNow(new Date());
    }, 1000);
    return () => window.clearInterval(clockTimer);
  }, []);

  useEffect(() => {
    const thoughtTimer = window.setInterval(() => {
      setThoughtIndex((current) =>
        pickDifferentIndex(thoughts.length, current),
      );
    }, THOUGHT_ROTATION_MS);
    return () => window.clearInterval(thoughtTimer);
  }, [thoughts.length]);

  const realTime = now
    ? now.toLocaleTimeString("en-CA", {
        timeZone: "America/Toronto",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
        hour12: false,
      })
    : "--:--:--";
  const dateLabel = now
    ? now.toLocaleDateString("en-CA", {
        timeZone: "America/Toronto",
        weekday: "short",
        month: "short",
        day: "numeric",
      })
    : "Toronto time";
  const secondProgress = now ? (now.getSeconds() / 60) * 100 : 0;
  const isExpanded = activeSection !== null;
  const activeSectionData = SECTIONS.find(
    (section) => section.id === activeSection,
  );

  const openSection = (sectionId: SidebarSectionId) => {
    setActiveSection((current) =>
      current === sectionId ? null : sectionId,
    );
  };

  const panelTitle =
    activeSectionData?.label ?? "Sidebar";

  return (
    <aside className={`sim-sidebar${isExpanded ? " expanded" : ""}`}>
      <div
        className="sidebar-panel"
        role="tabpanel"
        id={
          activeSectionData
            ? `sidebar-panel-${activeSectionData.id}`
            : undefined
        }
        aria-labelledby={
          activeSectionData
            ? `sidebar-tab-${activeSectionData.id}`
            : undefined
        }
        aria-hidden={!isExpanded}
      >
        <div className="sidebar-panel-inner">
          <p className="sidebar-label">{panelTitle}</p>

          {activeSection === "clock" ? (
            <>
              <div className="sidebar-clock-row">
                <span className="sidebar-clock">{realTime}</span>
                <span className="sidebar-clock-tag">LIVE</span>
              </div>
              <p className="sidebar-meta">{dateLabel}</p>
              <div className="sidebar-time-track" aria-hidden="true">
                <span style={{ width: `${secondProgress}%` }} />
              </div>
            </>
          ) : null}

          {activeSection === "thoughts" ? (
            <>
              <p className="sidebar-thought">
                {thoughts[thoughtIndex] ?? BASE_AGENT_THOUGHTS[0]}
              </p>
              <p className="sidebar-meta">Simulation status: {phase}</p>
              <button
                type="button"
                className="sidebar-secondary-btn"
                onClick={() =>
                  setThoughtIndex((current) =>
                    pickDifferentIndex(thoughts.length, current),
                  )
                }
              >
                Next thought
              </button>
            </>
          ) : null}

          {activeSection === "posts" ? (
            <>
              <p className="sidebar-meta">
                {posts.length > 0
                  ? `Showing ${Math.min(posts.length, 20)} most recent posts`
                  : "No posts yet"}
              </p>
              <TweetPanel />
            </>
          ) : null}
        </div>
      </div>

      <div
        className="sidebar-tabs"
        role="tablist"
        aria-label="Sidebar sections"
      >
        {SECTIONS.map((section) => {
          const isActive = activeSection === section.id;
          return (
            <button
              key={section.id}
              type="button"
              role="tab"
              id={`sidebar-tab-${section.id}`}
              aria-controls={`sidebar-panel-${section.id}`}
              aria-selected={isActive}
              title={section.label}
              className={`sidebar-tab${isActive ? " active" : ""}`}
              onClick={() => openSection(section.id)}
            >
              <SidebarTabIcon sectionId={section.id} />
              <span className="sidebar-sr-only">{section.label}</span>
            </button>
          );
        })}
      </div>
    </aside>
  );
}
