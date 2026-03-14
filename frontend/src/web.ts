/**
 * Web app entry: Mapbox Toronto map + city simulation. Map driven by engine state.
 */
import type { CityState } from "agentropolis";
import {
  SimulationEngine,
  DEFAULT_CITY_STATE,
  SAMPLE_EVENTS,
} from "agentropolis";
import { TorontoMapboxScene } from "./world/toronto-mapbox.js";

const logEntries: string[] = [];
const maxLogEntries = 50;

function log(msg: string, isEvent = false) {
  const entry = `${new Date().toLocaleTimeString()} ${msg}`;
  logEntries.unshift(entry);
  if (logEntries.length > maxLogEntries) logEntries.pop();
  renderLog();
}

function renderLog() {
  const el = document.getElementById("log");
  if (!el) return;
  el.innerHTML = logEntries
    .map((e) => `<div class="log-entry">${escapeHtml(e)}</div>`)
    .join("");
}

function escapeHtml(s: string): string {
  const div = document.createElement("div");
  div.textContent = s;
  return div.innerHTML;
}

function formatMetric(value: number, isPopulation = false): string {
  if (isPopulation) return value.toLocaleString();
  return Math.round(value).toString();
}

const STAT_PILLS: Array<{ key: keyof CityState; label: string }> = [
  { key: "economy", label: "Economy" },
  { key: "publicHealth", label: "Health" },
  { key: "pollution", label: "Pollution" },
];

function renderMetrics(state: Readonly<CityState>) {
  const statsEl = document.getElementById("stats");
  if (statsEl) {
    statsEl.innerHTML = STAT_PILLS.map(
      (p) =>
        `<span class="stat-pill"><span class="label">${escapeHtml(
          p.label
        )}</span><span class="value">${formatMetric(state[p.key])}</span></span>`
    ).join("");
  }
  const dayEl = document.getElementById("day-display");
  if (dayEl) dayEl.textContent = `Day ${engine.day}`;
  const popEl = document.getElementById("pop-display");
  if (popEl) popEl.textContent = `Pop. ${formatMetric(state.population, true)}`;
}

function onStep() {
  engine.step();
  log(`Day ${engine.day}`);
  renderMetrics(engine.state);
}

function onRun30() {
  engine.runDays(30);
  log(`Ran 30 days → Day ${engine.day}`);
  renderMetrics(engine.state);
}

function applyEvent(eventId: string) {
  const ev = SAMPLE_EVENTS[eventId];
  if (!ev) return;
  engine.applyEvent(ev);
  log(`Event: ${ev.name}`, true);
  renderMetrics(engine.state);
}

const engine = new SimulationEngine(
  { ...DEFAULT_CITY_STATE },
  {
    onStep(_prev, _next, _day) {},
    onEventApplied(_result, _day) {},
  }
);

const mapContainer = document.getElementById("canvas-container")!;

const torontoScene = new TorontoMapboxScene({ container: mapContainer });
torontoScene.startRenderLoop(() => ({
  state: engine.state,
  day: engine.day,
}));

document.getElementById("btn-step")!.addEventListener("click", onStep);
document.getElementById("btn-run-30")!.addEventListener("click", onRun30);

const eventsSheet = document.getElementById("events-sheet")!;
function toggleEventsSheet() {
  eventsSheet.classList.toggle("open");
}
document.getElementById("btn-events")!.addEventListener("click", toggleEventsSheet);

document.addEventListener("keydown", (e) => {
  if (e.key === " " && !e.repeat) {
    e.preventDefault();
    onStep();
  }
  if (e.key === "e" || e.key === "E") {
    const target = e.target as HTMLElement;
    if (target.tagName !== "INPUT" && target.tagName !== "TEXTAREA") {
      e.preventDefault();
      toggleEventsSheet();
    }
  }
});

const grid = document.getElementById("events-grid")!;
for (const [id, ev] of Object.entries(SAMPLE_EVENTS)) {
  const btn = document.createElement("button");
  btn.type = "button";
  btn.className = "event-btn";
  btn.innerHTML = `<span class="name">${escapeHtml(
    ev.name
  )}</span><span class="desc">${escapeHtml(ev.description ?? "")}</span>`;
  btn.addEventListener("click", () => applyEvent(id));
  grid.appendChild(btn);
}

log("Simulation started — Toronto (Mapbox).");
renderMetrics(engine.state);

