/**
 * Web app entry: 3D Toronto + city simulation frontend.
 * Uses the genai-genesis engine package and Three.js scene.
 */
import type { CityState } from "genai-genesis";
import {
  SimulationEngine,
  DEFAULT_CITY_STATE,
  SAMPLE_EVENTS,
} from "genai-genesis";
import { TorontoScene } from "./world/toronto-scene.js";

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

  const metricsEl = document.getElementById("metrics");
  if (metricsEl) metricsEl.innerHTML = metricsHtml;

  const dayPopEl = document.getElementById("day-pop");
  if (dayPopEl)
    dayPopEl.textContent = `Day ${engine.day} · Pop. ${formatMetric(state.population, true)}`;
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

const canvasContainer = document.getElementById("canvas-container")!;
const canvas = document.createElement("canvas");
canvas.id = "toronto-canvas";
canvasContainer.appendChild(canvas);

const torontoScene = new TorontoScene({ canvas });
torontoScene.startRenderLoop(() => ({
  state: engine.state,
  day: engine.day,
}));

document.getElementById("btn-step")!.addEventListener("click", onStep);
document.getElementById("btn-run-30")!.addEventListener("click", onRun30);

const grid = document.getElementById("events-grid")!;
for (const [id, ev] of Object.entries(SAMPLE_EVENTS)) {
  const btn = document.createElement("button");
  btn.type = "button";
  btn.className = "event-btn";
  btn.innerHTML = `<span class="name">${escapeHtml(ev.name)}</span><span class="desc">${escapeHtml(ev.description ?? "")}</span>`;
  btn.addEventListener("click", () => applyEvent(id));
  grid.appendChild(btn);
}

log("Simulation started — Toronto 3D.");
renderMetrics(engine.state);

