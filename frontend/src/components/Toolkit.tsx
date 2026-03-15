"use client";

import { useEffect, useMemo, useState, type ReactElement } from "react";
import type { ArchetypeResponse, PostResponse } from "../api/types";
import {
  useSimulationStore,
  type ToolkitTab,
} from "../store/simulationStore";
import type { MapFollower } from "../world/toronto-mapbox";

type ChartDatum = {
  label: string;
  value: number;
  color: string;
};

type ToolkitItem = {
  tab: ToolkitTab;
  label: string;
  shortLabel: string;
  Icon: (props: { active: boolean }) => ReactElement;
};

const PIE_COLORS = [
  "#38bdf8",
  "#34d399",
  "#f97316",
  "#facc15",
  "#fb7185",
  "#a78bfa",
  "#22d3ee",
  "#94a3b8",
];

const BAR_COLORS = ["#38bdf8", "#34d399", "#f97316", "#a78bfa"];

const TOOLKIT_ITEMS: ToolkitItem[] = [
  {
    tab: "latest_posts",
    label: "Latest Posts",
    shortLabel: "Posts",
    Icon: ({ active }) => (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path
          d="M5 6h14v9H9l-4 3V6z"
          fill="none"
          stroke="currentColor"
          strokeWidth={active ? "2.4" : "2"}
          strokeLinejoin="round"
        />
      </svg>
    ),
  },
  {
    tab: "demographics",
    label: "Demographics",
    shortLabel: "Demo",
    Icon: ({ active }) => (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <circle
          cx="12"
          cy="12"
          r="8"
          fill="none"
          stroke="currentColor"
          strokeWidth={active ? "2.4" : "2"}
        />
        <path
          d="M12 4v8l5.5 5.5"
          fill="none"
          stroke="currentColor"
          strokeWidth={active ? "2.4" : "2"}
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    ),
  },
  {
    tab: "archetypes",
    label: "Archetypes",
    shortLabel: "Arches",
    Icon: ({ active }) => (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <rect
          x="4"
          y="11"
          width="3.5"
          height="8"
          fill="currentColor"
          opacity={active ? "1" : "0.85"}
        />
        <rect
          x="10.25"
          y="7"
          width="3.5"
          height="12"
          fill="currentColor"
          opacity={active ? "1" : "0.85"}
        />
        <rect
          x="16.5"
          y="4"
          width="3.5"
          height="15"
          fill="currentColor"
          opacity={active ? "1" : "0.85"}
        />
      </svg>
    ),
  },
  {
    tab: "event_log",
    label: "Event Log",
    shortLabel: "Logs",
    Icon: ({ active }) => (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path
          d="M7 5h10M7 10h10M7 15h6"
          fill="none"
          stroke="currentColor"
          strokeWidth={active ? "2.4" : "2"}
          strokeLinecap="round"
        />
        <rect
          x="4"
          y="3"
          width="16"
          height="18"
          rx="2.5"
          fill="none"
          stroke="currentColor"
          strokeWidth={active ? "2.4" : "2"}
        />
      </svg>
    ),
  },
  {
    tab: "inject_event",
    label: "Inject Event",
    shortLabel: "Inject",
    Icon: ({ active }) => (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path
          d="M13 3L6 13h5l-1 8 8-11h-5l0-7z"
          fill="none"
          stroke="currentColor"
          strokeWidth={active ? "2.4" : "2"}
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    ),
  },
  {
    tab: "create_avatar",
    label: "Create Avatar",
    shortLabel: "Avatar",
    Icon: ({ active }) => (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <circle
          cx="12"
          cy="8"
          r="3.5"
          fill="none"
          stroke="currentColor"
          strokeWidth={active ? "2.4" : "2"}
        />
        <path
          d="M5 20a7 7 0 0 1 14 0"
          fill="none"
          stroke="currentColor"
          strokeWidth={active ? "2.4" : "2"}
          strokeLinecap="round"
        />
      </svg>
    ),
  },
];

function normalizeCategory(value: string | null | undefined): string {
  if (!value) return "Unknown";
  const trimmed = value.trim();
  if (!trimmed) return "Unknown";
  return trimmed
    .split(/[\s_-]+/)
    .map((part) =>
      part ? part[0].toUpperCase() + part.slice(1).toLowerCase() : "",
    )
    .join(" ");
}

function ageBucket(age: number | null | undefined): string {
  if (age == null || !Number.isFinite(age) || age < 0) return "Unknown";
  if (age < 18) return "<18";
  if (age <= 24) return "18-24";
  if (age <= 34) return "25-34";
  if (age <= 44) return "35-44";
  if (age <= 54) return "45-54";
  return "55+";
}

function countsToChartData(
  counts: Record<string, number>,
  colors: string[],
): ChartDatum[] {
  const rows = Object.entries(counts).filter(([, value]) => value > 0);
  rows.sort((a, b) => {
    if (a[0] === "Unknown") return 1;
    if (b[0] === "Unknown") return -1;
    return b[1] - a[1];
  });
  return rows.map(([label, value], index) => ({
    label,
    value,
    color: colors[index % colors.length],
  }));
}

function polarToCartesian(
  cx: number,
  cy: number,
  radius: number,
  angleRadians: number,
) {
  return {
    x: cx + radius * Math.cos(angleRadians),
    y: cy + radius * Math.sin(angleRadians),
  };
}

function describeArc(
  cx: number,
  cy: number,
  radius: number,
  startAngle: number,
  endAngle: number,
) {
  const start = polarToCartesian(cx, cy, radius, endAngle);
  const end = polarToCartesian(cx, cy, radius, startAngle);
  const largeArcFlag = endAngle - startAngle <= Math.PI ? "0" : "1";
  return `M ${cx} ${cy} L ${start.x} ${start.y} A ${radius} ${radius} 0 ${largeArcFlag} 0 ${end.x} ${end.y} Z`;
}

function PieChart({
  title,
  data,
  emptyLabel,
}: {
  title: string;
  data: ChartDatum[];
  emptyLabel: string;
}) {
  const total = data.reduce((sum, entry) => sum + entry.value, 0);

  return (
    <section className="toolkit-card">
      <h3>{title}</h3>
      {total === 0 ? (
        <p className="toolkit-empty">{emptyLabel}</p>
      ) : (
        <div className="toolkit-chart-grid">
          <svg
            className="toolkit-pie"
            viewBox="0 0 200 200"
            role="img"
            aria-label={`${title} pie chart`}
          >
            <circle cx="100" cy="100" r="80" fill="rgba(255,255,255,0.03)" />
            {data.length === 1 ? (
              <circle cx="100" cy="100" r="80" fill={data[0].color} />
            ) : (
              (() => {
                let startAngle = -Math.PI / 2;
                return data.map((entry) => {
                  const sweep = (entry.value / total) * Math.PI * 2;
                  const endAngle = startAngle + sweep;
                  const path = describeArc(
                    100,
                    100,
                    80,
                    startAngle,
                    endAngle,
                  );
                  startAngle = endAngle;
                  return (
                    <path
                      key={entry.label}
                      d={path}
                      fill={entry.color}
                      stroke="rgba(9, 9, 11, 0.9)"
                      strokeWidth="1.5"
                    />
                  );
                });
              })()
            )}
          </svg>
          <ul className="toolkit-legend">
            {data.map((entry) => {
              const percent = ((entry.value / total) * 100).toFixed(1);
              return (
                <li key={entry.label}>
                  <span
                    className="toolkit-legend-swatch"
                    style={{ backgroundColor: entry.color }}
                  />
                  <span className="toolkit-legend-label">{entry.label}</span>
                  <span className="toolkit-legend-value">
                    {entry.value} ({percent}%)
                  </span>
                </li>
              );
            })}
          </ul>
        </div>
      )}
    </section>
  );
}

function HorizontalBarChart({
  title,
  data,
  emptyLabel,
}: {
  title: string;
  data: ChartDatum[];
  emptyLabel: string;
}) {
  const max = Math.max(1, ...data.map((entry) => entry.value));
  const viewWidth = 460;
  const leftPadding = 126;
  const rightPadding = 56;
  const rowHeight = 28;
  const barHeight = 14;
  const topPadding = 10;
  const bottomPadding = 14;
  const innerWidth = viewWidth - leftPadding - rightPadding;
  const viewHeight = topPadding + bottomPadding + data.length * rowHeight;

  return (
    <section className="toolkit-card">
      <h3>{title}</h3>
      {data.length === 0 ? (
        <p className="toolkit-empty">{emptyLabel}</p>
      ) : (
        <svg
          className="toolkit-bar"
          viewBox={`0 0 ${viewWidth} ${viewHeight}`}
          role="img"
          aria-label={`${title} bar chart`}
        >
          {data.map((entry, index) => {
            const y = topPadding + index * rowHeight;
            const width = (entry.value / max) * innerWidth;
            return (
              <g key={entry.label}>
                <text
                  x="0"
                  y={y + barHeight - 1}
                  className="toolkit-svg-label"
                >
                  {entry.label}
                </text>
                <rect
                  x={leftPadding}
                  y={y}
                  width={width}
                  height={barHeight}
                  rx="5"
                  fill={entry.color}
                />
                <text
                  x={leftPadding + width + 8}
                  y={y + barHeight - 1}
                  className="toolkit-svg-value"
                >
                  {entry.value}
                </text>
              </g>
            );
          })}
        </svg>
      )}
    </section>
  );
}

function LatestPostsTab({ posts }: { posts: PostResponse[] }) {
  const followers = useSimulationStore((state) => state.followers);
  const nameMap = useMemo(() => {
    const m = new Map<number, string>();
    for (const f of followers) m.set(f.follower_id, f.name);
    return m;
  }, [followers]);

  return (
    <section className="toolkit-card">
      <h3>Latest Posts</h3>
      <div className="toolkit-scroll">
        {posts.slice(0, 20).map((post) => (
          <article key={post.post_id} className="toolkit-post">
            <span className="toolkit-post-author">
              {nameMap.get(post.follower_id) ?? `Follower #${post.follower_id}`}
            </span>
            <span className="toolkit-post-text">{post.text}</span>
            <span className="toolkit-post-time">
              {new Date(post.virtual_time).toLocaleTimeString("en-CA", {
                timeZone: "America/Toronto",
                hour: "2-digit",
                minute: "2-digit",
                hour12: false,
              })}
            </span>
          </article>
        ))}
        {posts.length === 0 && (
          <p className="toolkit-empty">No posts yet. Run a tick to generate activity.</p>
        )}
      </div>
    </section>
  );
}

function DemographicsTab({ followers }: { followers: MapFollower[] }) {
  const { genderChart, raceChart, ageChart } = useMemo(() => {
    const genderCounts: Record<string, number> = {};
    const raceCounts: Record<string, number> = {};
    const ageCounts: Record<string, number> = {
      "<18": 0,
      "18-24": 0,
      "25-34": 0,
      "35-44": 0,
      "45-54": 0,
      "55+": 0,
      Unknown: 0,
    };

    for (const follower of followers) {
      const gender = normalizeCategory(follower.gender);
      genderCounts[gender] = (genderCounts[gender] ?? 0) + 1;

      const race = normalizeCategory(follower.race);
      raceCounts[race] = (raceCounts[race] ?? 0) + 1;

      const bucket = ageBucket(follower.age);
      ageCounts[bucket] = (ageCounts[bucket] ?? 0) + 1;
    }

    return {
      genderChart: countsToChartData(genderCounts, PIE_COLORS),
      raceChart: countsToChartData(raceCounts, PIE_COLORS),
      ageChart: countsToChartData(ageCounts, BAR_COLORS),
    };
  }, [followers]);

  return (
    <div className="toolkit-stack">
      <PieChart
        title="Gender Distribution"
        data={genderChart}
        emptyLabel="No gender data available."
      />
      <PieChart
        title="Race Distribution"
        data={raceChart}
        emptyLabel="No race data available."
      />
      <HorizontalBarChart
        title="Age Buckets"
        data={ageChart}
        emptyLabel="No age data available."
      />
    </div>
  );
}

function ArchetypesTab({ archetypes }: { archetypes: ArchetypeResponse[] }) {
  const chartData = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const archetype of archetypes) {
      const industry = normalizeCategory(archetype.industry);
      counts[industry] = (counts[industry] ?? 0) + archetype.follower_count;
    }
    return countsToChartData(counts, BAR_COLORS);
  }, [archetypes]);

  return (
    <HorizontalBarChart
      title="Followers by Industry"
      data={chartData}
      emptyLabel="No archetype data available."
    />
  );
}

function EventLogTab({ logEntries }: { logEntries: string[] }) {
  return (
    <section className="toolkit-card">
      <h3>Event Log</h3>
      <div className="toolkit-scroll toolkit-log">
        {logEntries.map((entry, index) => (
          <div key={`${entry}-${index}`} className="toolkit-log-entry">
            {entry}
          </div>
        ))}
        {logEntries.length === 0 && (
          <p className="toolkit-empty">No log entries yet.</p>
        )}
      </div>
    </section>
  );
}

function InjectEventTab() {
  const phase = useSimulationStore((state) => state.phase);
  const injectEvent = useSimulationStore((state) => state.injectEvent);
  const log = useSimulationStore((state) => state.log);
  const [eventText, setEventText] = useState("");

  const canSubmit = phase === "ready" || phase === "auto_running";

  const handleSubmit = () => {
    const prompt = eventText.trim();
    if (!prompt) return;
    if (prompt.length > 1000) {
      log("Event text too long (max 1000 chars)");
      return;
    }
    injectEvent(prompt);
    setEventText("");
  };

  return (
    <section className="toolkit-card">
      <h3>Inject Event</h3>
      <p className="toolkit-muted">
        Add a narrative city event that influences the next simulation tick.
      </p>
      <div className="event-input">
        <textarea
          placeholder="Describe a city event (max 1000 chars)..."
          maxLength={1000}
          rows={4}
          value={eventText}
          onChange={(event) => setEventText(event.target.value)}
        />
        <button
          type="button"
          className="btn btn-primary"
          disabled={!canSubmit}
          onClick={handleSubmit}
        >
          Inject
        </button>
      </div>
    </section>
  );
}

function CreateAvatarTab() {
  const createFollowerWithAvatar = useSimulationStore(
    (state) => state.createFollowerWithAvatar,
  );
  const log = useSimulationStore((state) => state.log);
  const session = useSimulationStore((state) => state.session);

  const [name, setName] = useState("You");
  const [skinTone, setSkinTone] = useState(40);
  const [bodyType, setBodyType] = useState("average");
  const [hairTexture, setHairTexture] = useState("straight");
  const [hairStyle, setHairStyle] = useState("short");
  const [hairColor, setHairColor] = useState("#4a3728");
  const [outfit, setOutfit] = useState("casual");
  const [outfitColor, setOutfitColor] = useState("#2c3e50");
  const [glasses, setGlasses] = useState(false);
  const [hat, setHat] = useState(false);
  const [bag, setBag] = useState(false);
  const [scarf, setScarf] = useState(false);

  const handleJoin = async () => {
    if (!session) {
      log("No session; start simulation first.");
      return;
    }

    const accessories = [
      glasses && "glasses",
      hat && "hat",
      bag && "bag",
      scarf && "scarf",
    ].filter(Boolean) as string[];

    try {
      await createFollowerWithAvatar(name.trim() || "You", {
        skinTone: skinTone / 100,
        bodyType,
        hairTexture,
        hairStyle,
        hairColor,
        outfit,
        outfitColor,
        accessories,
      });
    } catch (error) {
      log(`Error: ${error instanceof Error ? error.message : String(error)}`);
    }
  };

  return (
    <section className="toolkit-card">
      <h3>Create Your Avatar</h3>
      <p className="avatar-desc">
        Join the simulation with a custom avatar. No photos, just style and
        color choices.
      </p>
      <div className="avatar-form">
        <label>
          Name{" "}
          <input
            type="text"
            value={name}
            onChange={(event) => setName(event.target.value)}
            maxLength={128}
          />
        </label>
        <label>
          Skin tone{" "}
          <input
            type="range"
            min={0}
            max={100}
            value={skinTone}
            onChange={(event) => setSkinTone(Number(event.target.value))}
          />{" "}
          <span>{(skinTone / 100).toFixed(2)}</span>
        </label>
        <label>
          Body{" "}
          <select value={bodyType} onChange={(event) => setBodyType(event.target.value)}>
            <option value="slim">Slim</option>
            <option value="average">Average</option>
            <option value="broad">Broad</option>
          </select>
        </label>
        <label>
          Hair texture{" "}
          <select
            value={hairTexture}
            onChange={(event) => setHairTexture(event.target.value)}
          >
            <option value="straight">Straight</option>
            <option value="wavy">Wavy</option>
            <option value="curly">Curly</option>
            <option value="coily">Coily</option>
          </select>
        </label>
        <label>
          Hair style{" "}
          <select
            value={hairStyle}
            onChange={(event) => setHairStyle(event.target.value)}
          >
            <option value="short">Short</option>
            <option value="long">Long</option>
            <option value="fade">Fade</option>
            <option value="bun">Bun</option>
            <option value="braids">Braids</option>
            <option value="afro">Afro</option>
            <option value="ponytail">Ponytail</option>
          </select>
        </label>
        <label>
          Hair color{" "}
          <input
            type="color"
            value={hairColor}
            onChange={(event) => setHairColor(event.target.value)}
          />
        </label>
        <label>
          Outfit{" "}
          <select value={outfit} onChange={(event) => setOutfit(event.target.value)}>
            <option value="casual">Casual</option>
            <option value="professional">Professional</option>
            <option value="student">Student</option>
            <option value="athletic">Athletic</option>
            <option value="construction">Construction</option>
            <option value="service">Service</option>
          </select>
        </label>
        <label>
          Outfit color{" "}
          <input
            type="color"
            value={outfitColor}
            onChange={(event) => setOutfitColor(event.target.value)}
          />
        </label>
        <fieldset className="avatar-accessories">
          <legend>Accessories</legend>
          <label>
            <input
              type="checkbox"
              checked={glasses}
              onChange={(event) => setGlasses(event.target.checked)}
            />{" "}
            Glasses
          </label>
          <label>
            <input
              type="checkbox"
              checked={hat}
              onChange={(event) => setHat(event.target.checked)}
            />{" "}
            Hat
          </label>
          <label>
            <input
              type="checkbox"
              checked={bag}
              onChange={(event) => setBag(event.target.checked)}
            />{" "}
            Bag
          </label>
          <label>
            <input
              type="checkbox"
              checked={scarf}
              onChange={(event) => setScarf(event.target.checked)}
            />{" "}
            Scarf
          </label>
        </fieldset>
        <div className="avatar-preview" style={{ backgroundColor: outfitColor }} />
        <button
          type="button"
          className="btn btn-primary btn-avatar-join"
          onClick={handleJoin}
        >
          Join simulation
        </button>
      </div>
    </section>
  );
}

function ToolkitContent({ tab }: { tab: ToolkitTab }) {
  const posts = useSimulationStore((state) => state.posts);
  const followers = useSimulationStore((state) => state.followers);
  const archetypes = useSimulationStore((state) => state.archetypes);
  const logEntries = useSimulationStore((state) => state.logEntries);

  if (tab === "latest_posts") {
    return <LatestPostsTab posts={posts} />;
  }
  if (tab === "demographics") {
    return <DemographicsTab followers={followers} />;
  }
  if (tab === "archetypes") {
    return <ArchetypesTab archetypes={archetypes} />;
  }
  if (tab === "event_log") {
    return <EventLogTab logEntries={logEntries} />;
  }
  if (tab === "inject_event") {
    return <InjectEventTab />;
  }
  return <CreateAvatarTab />;
}

export default function Toolkit() {
  const activeToolkitTab = useSimulationStore((state) => state.activeToolkitTab);
  const setToolkitTab = useSimulationStore((state) => state.setToolkitTab);
  const isToolkitOpenMobile = useSimulationStore(
    (state) => state.isToolkitOpenMobile,
  );
  const toggleToolkitMobile = useSimulationStore(
    (state) => state.toggleToolkitMobile,
  );
  const [desktopCollapsed, setDesktopCollapsed] = useState(false);

  useEffect(() => {
    setDesktopCollapsed(false);
  }, [activeToolkitTab]);

  const activeLabel =
    TOOLKIT_ITEMS.find((item) => item.tab === activeToolkitTab)?.label ??
    "Toolkit";

  const onDesktopTabPress = (tab: ToolkitTab) => {
    if (tab === activeToolkitTab) {
      setDesktopCollapsed((current) => !current);
      return;
    }
    setToolkitTab(tab);
  };

  const onMobileTabPress = (tab: ToolkitTab) => {
    setToolkitTab(tab);
  };

  return (
    <>
      <div className="toolkit-layer toolkit-desktop-shell" aria-label="Toolkit">
        <aside className="toolkit-rail">
          {TOOLKIT_ITEMS.map((item) => {
            const isActive = item.tab === activeToolkitTab;
            return (
              <button
                key={item.tab}
                type="button"
                className={`toolkit-rail-btn${isActive ? " active" : ""}`}
                onClick={() => onDesktopTabPress(item.tab)}
                aria-label={item.label}
                title={item.label}
              >
                <item.Icon active={isActive} />
              </button>
            );
          })}
        </aside>
        <section className={`toolkit-panel${desktopCollapsed ? " collapsed" : ""}`}>
          {!desktopCollapsed && <ToolkitContent tab={activeToolkitTab} />}
        </section>
      </div>

      <div className={`toolkit-mobile-shell${isToolkitOpenMobile ? " open" : ""}`}>
        <button
          type="button"
          className="toolkit-mobile-backdrop"
          aria-label="Close Toolkit"
          onClick={toggleToolkitMobile}
        />
        <section className="toolkit-mobile-drawer" aria-label="Toolkit">
          <header className="toolkit-mobile-header">
            <h2>{activeLabel}</h2>
            <button type="button" className="btn" onClick={toggleToolkitMobile}>
              Close
            </button>
          </header>
          <nav className="toolkit-mobile-tabs" aria-label="Toolkit tabs">
            {TOOLKIT_ITEMS.map((item) => {
              const isActive = item.tab === activeToolkitTab;
              return (
                <button
                  key={item.tab}
                  type="button"
                  className={`toolkit-mobile-tab${isActive ? " active" : ""}`}
                  onClick={() => onMobileTabPress(item.tab)}
                >
                  <item.Icon active={isActive} />
                  <span>{item.shortLabel}</span>
                </button>
              );
            })}
          </nav>
          <div className="toolkit-mobile-content">
            <ToolkitContent tab={activeToolkitTab} />
          </div>
        </section>
      </div>
    </>
  );
}
