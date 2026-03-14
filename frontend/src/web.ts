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
  // Prepend newest entry instead of rebuilding entire DOM
  const newest = logEntries[0];
  if (!newest) return;
  const div = document.createElement("div");
  div.className = "log-entry";
  div.textContent = newest;
  el.insertBefore(div, el.firstChild);
  // Trim excess entries from DOM
  while (el.children.length > maxLogEntries) {
    el.removeChild(el.lastChild!);
  }
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
  // Clear and rebuild with DOM nodes (avoids innerHTML reparse)
  container.textContent = "";
  for (const p of posts.slice(0, 20)) {
    const div = document.createElement("div");
    div.className = "tweet";
    const author = document.createElement("span");
    author.className = "tweet-author";
    author.textContent = `Follower #${p.follower_id}`;
    const text = document.createElement("span");
    text.className = "tweet-text";
    text.textContent = p.text;
    const time = document.createElement("span");
    time.className = "tweet-time";
    time.textContent = new Date(p.virtual_time).toLocaleTimeString();
    div.append(author, text, time);
    container.appendChild(div);
  }
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

const avatarSheet = document.getElementById("avatar-sheet")!;
function toggleAvatarSheet() {
  avatarSheet.classList.toggle("open");
}
document.getElementById("btn-avatar")!.addEventListener("click", toggleAvatarSheet);

function getAvatarParamsFromForm(): {
  name: string;
  skinTone: number;
  bodyType: string;
  hairTexture: string;
  hairStyle: string;
  hairColor: string;
  outfit: string;
  outfitColor: string;
  accessories: string[];
} {
  const nameEl = document.getElementById("avatar-name") as HTMLInputElement;
  const skintoneEl = document.getElementById("avatar-skintone") as HTMLInputElement;
  const bodyEl = document.getElementById("avatar-body") as HTMLSelectElement;
  const hairTexEl = document.getElementById("avatar-hair-texture") as HTMLSelectElement;
  const hairStyleEl = document.getElementById("avatar-hair-style") as HTMLSelectElement;
  const hairColorEl = document.getElementById("avatar-hair-color") as HTMLInputElement;
  const outfitEl = document.getElementById("avatar-outfit") as HTMLSelectElement;
  const outfitColorEl = document.getElementById("avatar-outfit-color") as HTMLInputElement;
  const acc = [
    (document.getElementById("acc-glasses") as HTMLInputElement)?.checked && "glasses",
    (document.getElementById("acc-hat") as HTMLInputElement)?.checked && "hat",
    (document.getElementById("acc-bag") as HTMLInputElement)?.checked && "bag",
    (document.getElementById("acc-scarf") as HTMLInputElement)?.checked && "scarf",
  ].filter(Boolean) as string[];
  return {
    name: (nameEl?.value ?? "You").trim() || "You",
    skinTone: Number(skintoneEl?.value ?? 40) / 100,
    bodyType: bodyEl?.value ?? "average",
    hairTexture: hairTexEl?.value ?? "straight",
    hairStyle: hairStyleEl?.value ?? "short",
    hairColor: hairColorEl?.value ?? "#4a3728",
    outfit: outfitEl?.value ?? "casual",
    outfitColor: outfitColorEl?.value ?? "#2c3e50",
    accessories: acc,
  };
}

function updateAvatarPreview() {
  const p = getAvatarParamsFromForm();
  const el = document.getElementById("avatar-preview");
  if (el) el.style.backgroundColor = p.outfitColor;
}
["avatar-skintone", "avatar-body", "avatar-hair-texture", "avatar-hair-style", "avatar-hair-color", "avatar-outfit", "avatar-outfit-color"].forEach((id) => {
  const el = document.getElementById(id);
  el?.addEventListener("input", updateAvatarPreview);
  el?.addEventListener("change", updateAvatarPreview);
});
document.getElementById("avatar-skintone")?.addEventListener("input", () => {
  const v = (document.getElementById("avatar-skintone") as HTMLInputElement).value;
  const valEl = document.getElementById("avatar-skintone-val");
  if (valEl) valEl.textContent = (Number(v) / 100).toFixed(2);
});

document.getElementById("btn-avatar-join")?.addEventListener("click", async () => {
  const session = controller.getSession();
  if (!session) {
    log("No session; start simulation first.");
    return;
  }
  const p = getAvatarParamsFromForm();
  try {
    await controller.createFollowerWithAvatar(p.name, {
      skinTone: p.skinTone,
      bodyType: p.bodyType,
      hairTexture: p.hairTexture,
      hairStyle: p.hairStyle,
      hairColor: p.hairColor,
      outfit: p.outfit,
      outfitColor: p.outfitColor,
      accessories: p.accessories,
    });
    toggleAvatarSheet();
  } catch (err) {
    log(`Error: ${err instanceof Error ? err.message : String(err)}`);
  }
});

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
  if (e.key === "a" || e.key === "A") {
    const target = e.target as HTMLElement;
    if (target.tagName !== "INPUT" && target.tagName !== "TEXTAREA") {
      e.preventDefault();
      toggleAvatarSheet();
    }
  }
});

// ── Welcome screen ──

const welcomeScreen = document.getElementById("welcome-screen")!;
const btnWelcomeStart = document.getElementById("btn-welcome-start")!;

btnWelcomeStart.addEventListener("click", () => {
  welcomeScreen.classList.add("hidden");
  log("Initializing Agentropolis...");
  controller.createAndConnect();
});

updateAvatarPreview();
