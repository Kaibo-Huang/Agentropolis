/**
 * Web app entry: runs the city simulation and renders state + events.
 */
import type { CityState } from "./types/city-state.js";
import {
  SimulationEngine,
  DEFAULT_CITY_STATE,
  SAMPLE_EVENTS,
} from "./index.js";

const app = document.getElementById("app")!;
const logEntries: string[] = [];
const maxLogEntries = 50;

function log(msg: string, isEvent = false) {
  const cls = isEvent ? "event" : "";
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

function renderMetrics(state: Readonly<CityState>) {
  const metrics = [
    { key: "economy", label: "Economy", value: state.economy, class: "economy" },
    {
      key: "publicHealth",
      label: "Public health",
      value: state.publicHealth,
      class: "publicHealth",
    },
    {
      key: "housingCost",
      label: "Housing cost",
      value: state.housingCost,
      class: "housingCost",
    },
    { key: "pollution", label: "Pollution", value: state.pollution, class: "pollution" },
    {
      key: "publicOpinion",
      label: "Public opinion",
      value: state.publicOpinion,
      class: "publicOpinion",
    },
  ];

  const metricsHtml = metrics
    .map(
      (m) => `
    <div class="metric ${m.class}">
      <div class="label">${escapeHtml(m.label)}</div>
      <div class="value">${formatMetric(m.value)}</div>
      <div class="bar-wrap"><div class="bar" style="width:${m.value}%"></div></div>
    </div>
  `
    )
    .join("");

  const dayBar = `
    <div class="day-bar">
      <span class="day">Day ${engine.day}</span>
      <span class="population">Population ${formatMetric(state.population, true)}</span>
    </div>
  `;

  const controls = `
    <div class="controls">
      <button type="button" class="primary" id="btn-step">Advance 1 day</button>
      <button type="button" id="btn-run-30">Run 30 days</button>
    </div>
  `;

  const eventsSection = `
    <section class="events-section">
      <h2>Apply event</h2>
      <div class="events-grid" id="events-grid"></div>
    </section>
  `;

  const logSection = `
    <div class="log" id="log"></div>
  `;

  app.innerHTML = `
    <h1>GenAI Genesis</h1>
    <p class="subtitle">City state simulation — advance days and apply events.</p>
    ${dayBar}
    ${controls}
    <div class="metrics">${metricsHtml}</div>
    ${eventsSection}
    ${logSection}
  `;

  document.getElementById("btn-step")!.addEventListener("click", onStep);
  document.getElementById("btn-run-30")!.addEventListener("click", onRun30);

  const grid = document.getElementById("events-grid")!;
  for (const [id, ev] of Object.entries(SAMPLE_EVENTS)) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "event-btn";
    btn.dataset.eventId = id;
    btn.innerHTML = `<span class="name">${escapeHtml(ev.name)}</span><span class="desc">${escapeHtml(ev.description ?? "")}</span>`;
    btn.addEventListener("click", () => applyEvent(id));
    grid.appendChild(btn);
  }

  renderLog();
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
    onStep(prev, next, day) {
      // optional: fine-grained log per step
    },
    onEventApplied(result, day) {
      // already logged in applyEvent()
    },
  }
);

log("Simulation started.");
renderMetrics(engine.state);
