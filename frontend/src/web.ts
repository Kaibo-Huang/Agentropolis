/**
 * Web app entry: Mapbox Toronto map + backend-driven simulation.
 * Replaces local SimulationEngine with SessionController (REST + WebSocket).
 */
import { SessionController } from "./state/session.js";
import type { ControllerPhase } from "./state/session.js";
import type {
  SessionResponse,
  PostResponse,
  ArchetypeResponse,
  TickResponse,
} from "./api/types.js";
import type { MapFollower } from "./world/toronto-mapbox.js";
import { TorontoMapboxScene } from "./world/toronto-mapbox.js";

// ── Configuration ──

const API_BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
const WS_BASE = API_BASE.replace(/^http/, "ws");

// ── Log ──

const logEntries: string[] = [];
const maxLogEntries = 50;

function log(msg: string) {
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

// ── Map ──

const mapContainer = document.getElementById("canvas-container")!;
const torontoScene = new TorontoMapboxScene({ container: mapContainer });

// ── Session Controller ──

const controller = new SessionController(API_BASE, WS_BASE, {
  onPhaseChange(phase: ControllerPhase) {
    updateButtonStates(phase);
  },
  onSessionUpdate(session: SessionResponse) {
    renderSessionInfo(session);
  },
  onFollowersUpdate(followers: MapFollower[]) {
    torontoScene.setFollowers(followers);
    const popEl = document.getElementById("pop-display");
    if (popEl) popEl.textContent = `Pop. ${followers.length.toLocaleString()}`;
  },
  onArchetypesUpdate(_archetypes: ArchetypeResponse[]) {
    // Could render archetype legend in the future
  },
  onPostsUpdate(posts: PostResponse[]) {
    renderTweets(posts);
  },
  onTickComplete(tick: TickResponse) {
    log(
      `Tick ${tick.tick_number} complete (${tick.archetypes_processed} OK, ${tick.archetypes_failed} failed)`,
    );
  },
  onError(err: Error) {
    log(`Error: ${err.message}`);
  },
  onLog(msg: string) {
    log(msg);
  },
});

// ── Render loop ──

torontoScene.startRenderLoop(() => controller.getHourOfDay());

// ── UI Rendering ──

function renderSessionInfo(session: SessionResponse) {
  const dayEl = document.getElementById("day-display");
  if (dayEl) {
    const vt = new Date(session.virtual_time);
    dayEl.textContent = vt.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
      timeZone: "UTC",
    });
  }
}

function renderTweets(posts: PostResponse[]) {
  const container = document.getElementById("tweets-list");
  if (!container) return;
  container.innerHTML = posts
    .slice(0, 20)
    .map(
      (p) =>
        `<div class="tweet">
       <span class="tweet-author">Follower #${p.follower_id}</span>
       <span class="tweet-text">${escapeHtml(p.text)}</span>
       <span class="tweet-time">${new Date(p.virtual_time).toLocaleTimeString()}</span>
     </div>`,
    )
    .join("");
}

function updateButtonStates(phase: ControllerPhase) {
  const btnStep = document.getElementById("btn-step") as HTMLButtonElement;
  const btnAutoRun = document.getElementById(
    "btn-auto-run",
  ) as HTMLButtonElement;
  const btnEventSubmit = document.getElementById(
    "btn-event-submit",
  ) as HTMLButtonElement | null;

  const canTick = phase === "ready";
  const isAutoRunning = phase === "auto_running";

  if (btnStep) btnStep.disabled = !canTick;
  if (btnAutoRun) {
    btnAutoRun.textContent = isAutoRunning ? "Stop" : "Auto-Run";
    btnAutoRun.disabled = phase !== "ready" && phase !== "auto_running";
  }
  if (btnEventSubmit)
    btnEventSubmit.disabled = !canTick && !isAutoRunning;
}

// ── Button handlers ──

document.getElementById("btn-step")!.addEventListener("click", () => {
  controller.tickOnce();
});

document.getElementById("btn-auto-run")!.addEventListener("click", () => {
  if (controller.getPhase() === "auto_running") {
    controller.stopAutoRun();
  } else {
    controller.startAutoRun();
  }
});

const eventsSheet = document.getElementById("events-sheet")!;
function toggleEventsSheet() {
  eventsSheet.classList.toggle("open");
}
document
  .getElementById("btn-events")!
  .addEventListener("click", toggleEventsSheet);

document.getElementById("btn-event-submit")?.addEventListener("click", () => {
  const textarea = document.getElementById(
    "event-textarea",
  ) as HTMLTextAreaElement;
  const prompt = textarea.value.trim();
  if (!prompt) return;
  if (prompt.length > 1000) {
    log("Event text too long (max 1000 chars)");
    return;
  }
  controller.injectEvent(prompt);
  textarea.value = "";
});

// ── Keyboard shortcuts ──

document.addEventListener("keydown", (e) => {
  if (e.key === " " && !e.repeat) {
    e.preventDefault();
    controller.tickOnce();
  }
  if (e.key === "e" || e.key === "E") {
    const target = e.target as HTMLElement;
    if (target.tagName !== "INPUT" && target.tagName !== "TEXTAREA") {
      e.preventDefault();
      toggleEventsSheet();
    }
  }
});

// ── Bootstrap ──

log("Initializing Agentropolis...");
controller.createAndConnect();
