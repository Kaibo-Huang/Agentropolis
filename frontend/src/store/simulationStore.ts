import { create } from "zustand";
import { ApiClient } from "../api/client";
import { SimulationSocket } from "../api/client";
import type {
  SessionResponse,
  ArchetypeResponse,
  PostResponse,
  AvatarParamsResponse,
} from "../api/types";
import type { MapFollower } from "../world/toronto-mapbox";
import { resolveAvatar } from "../avatar/resolveAvatar";
import type { FollowerResponse, LngLat } from "../api/types";

// ── Pure helpers (ported from state/session.ts) ──

/** Convert backend [lat, lng] to Mapbox [lng, lat]. */
function toMapbox(backendPos: [number, number] | null): LngLat | null {
  if (!backendPos) return null;
  return [backendPos[1], backendPos[0]];
}

function toMapFollower(f: FollowerResponse): MapFollower {
  const avatar = resolveAvatar(f.avatar_seed ?? null, f.avatar_params ?? null);
  return {
    follower_id: f.follower_id,
    archetype_id: f.archetype_id,
    name: f.name,
    position: toMapbox(f.position),
    happiness: f.happiness,
    avatar: avatar ?? undefined,
  };
}

// ── Types ──

export type ControllerPhase =
  | "idle"
  | "loading"
  | "ready"
  | "ticking"
  | "auto_running"
  | "error";

const MAX_LOG_ENTRIES = 50;
const MAX_CONSECUTIVE_FAILURES = 3;

export interface SimulationState {
  // Data
  phase: ControllerPhase;
  session: SessionResponse | null;
  followers: MapFollower[];
  archetypes: ArchetypeResponse[];
  posts: PostResponse[];
  logEntries: string[];
  hourOfDay: number;

  // UI state
  showWelcome: boolean;
  showEventsSheet: boolean;
  showAvatarSheet: boolean;

  // Actions
  createAndConnect: () => Promise<void>;
  tickOnce: () => Promise<void>;
  startAutoRun: () => void;
  stopAutoRun: () => void;
  injectEvent: (prompt: string) => Promise<void>;
  createFollowerWithAvatar: (
    name: string,
    params: {
      skinTone: number;
      bodyType: string;
      hairTexture: string;
      hairStyle: string;
      hairColor: string;
      outfit: string;
      outfitColor: string;
      accessories: string[];
    },
  ) => Promise<void>;
  disconnect: () => Promise<void>;
  toggleEventsSheet: () => void;
  toggleAvatarSheet: () => void;
  dismissWelcome: () => void;
  log: (msg: string) => void;
}

// ── Store ──

const API_BASE =
  (typeof process !== "undefined" &&
    process.env.NEXT_PUBLIC_API_URL) ||
  "http://localhost:8000";
const WS_BASE = API_BASE.replace(/^http/, "ws");

// Closure state (not serializable, not part of React state)
let api: ApiClient = new ApiClient(API_BASE);
let socket: SimulationSocket | null = null;
let autoRunTimer: ReturnType<typeof setTimeout> | null = null;
let ticking = false;
let consecutiveFailures = 0;

export const useSimulationStore = create<SimulationState>((set, get) => {
  function log(msg: string) {
    const entry = `${new Date().toLocaleTimeString()} ${msg}`;
    set((s) => ({
      logEntries: [entry, ...s.logEntries].slice(0, MAX_LOG_ENTRIES),
    }));
  }

  function computeHourOfDay(session: SessionResponse | null): number {
    if (!session) return 8;
    const vt = new Date(session.virtual_time);
    const torontoHour = vt.toLocaleString("en-CA", {
      timeZone: "America/Toronto",
      hour: "numeric",
      hour12: false,
    });
    return parseInt(torontoHour, 10) || 0;
  }

  async function autoRunLoop() {
    const { phase } = get();
    if (phase !== "auto_running") return;
    await get().tickOnce();
    if (get().phase !== "auto_running") return;
    autoRunTimer = setTimeout(autoRunLoop, 2000);
  }

  return {
    // Initial state
    phase: "idle",
    session: null,
    followers: [],
    archetypes: [],
    posts: [],
    logEntries: [],
    hourOfDay: 8,
    showWelcome: true,
    showEventsSheet: false,
    showAvatarSheet: false,

    // Actions
    log,

    async createAndConnect() {
      set({ phase: "loading" });
      let sessionId: string | null = null;
      try {
        // 1. Create session
        const session = await api.createSession();
        sessionId = session.session_id;
        set({ session, hourOfDay: computeHourOfDay(session) });
        log(`Session created: ${session.session_id.substring(0, 8)}...`);

        // 2. Resume (paused -> running)
        const resumed = await api.resumeSession(session.session_id);
        set({ session: resumed, hourOfDay: computeHourOfDay(resumed) });

        // 3. Connect WebSocket
        socket = new SimulationSocket(
          WS_BASE,
          session.session_id,
          (msg) => {
            if (msg.type === "subscribed") {
              log("WebSocket subscribed");
            } else if (msg.type === "error") {
              log(`WS error: ${msg.data.message}`);
            }
          },
          (state) => log(`WS: ${state}`),
        );
        socket.connect();

        // 4. Fetch initial data in parallel
        const [followerRes, archetypeRes, postRes] = await Promise.all([
          api.getFollowers(session.session_id, 0, 200),
          api.getArchetypes(session.session_id),
          api.getPosts(session.session_id, 0, 20),
        ]);

        const followers = followerRes.followers.map(toMapFollower);
        set({
          followers,
          archetypes: archetypeRes.archetypes,
          posts: postRes.posts,
          phase: "ready",
        });
        log(
          `Ready: ${followers.length} followers, ${archetypeRes.archetypes.length} archetypes`,
        );
      } catch (err) {
        // Cleanup orphaned session if it was created
        if (sessionId) {
          try {
            await api.deleteSession(sessionId);
          } catch {
            // best-effort cleanup
          }
        }
        set({ phase: "error" });
        const message =
          err instanceof Error ? err.message : String(err);
        log(`Error: ${message}`);
      }
    },

    async tickOnce() {
      const { session, phase } = get();
      if (
        !session ||
        (phase !== "ready" && phase !== "auto_running")
      )
        return;
      if (ticking) return; // prevent concurrent ticks

      const prevPhase = phase;
      if (prevPhase === "ready") set({ phase: "ticking" });
      ticking = true;

      try {
        // Compute target_time = current virtual_time + 1 hour
        const currentVt = new Date(session.virtual_time);
        const targetVt = new Date(currentVt.getTime() + 3_600_000);

        const tickResult = await api.tick(session.session_id, {
          target_time: targetVt.toISOString(),
        });

        // Refresh session state + followers + posts in parallel
        const [sessionRes, followerRes, postRes] = await Promise.all([
          api.getSession(session.session_id),
          api.getFollowers(session.session_id, 0, 200),
          api.getPosts(session.session_id, 0, 20),
        ]);

        const followers = followerRes.followers.map(toMapFollower);
        set({
          session: sessionRes,
          followers,
          posts: postRes.posts,
          hourOfDay: computeHourOfDay(sessionRes),
        });

        const vtDisplay = new Date(
          sessionRes.virtual_time,
        ).toLocaleString("en-CA", { timeZone: "America/Toronto" });
        log(
          `Tick ${tickResult.tick_number}: ${vtDisplay} (${tickResult.archetypes_processed} OK, ${tickResult.archetypes_failed} fail)`,
        );

        consecutiveFailures = 0;
        if (prevPhase === "ready") set({ phase: "ready" });
      } catch (err) {
        const message =
          err instanceof Error ? err.message : String(err);
        log(`Error: ${message}`);

        consecutiveFailures++;
        if (
          prevPhase === "auto_running" &&
          consecutiveFailures >= MAX_CONSECUTIVE_FAILURES
        ) {
          log(
            `Auto-run stopped after ${MAX_CONSECUTIVE_FAILURES} consecutive failures`,
          );
          get().stopAutoRun();
        } else if (prevPhase === "ready") {
          set({ phase: "ready" });
        } else if (prevPhase === "auto_running") {
          // Restore auto_running so the loop continues (under max failures)
          set({ phase: "auto_running" });
        }
      } finally {
        ticking = false;
      }
    },

    startAutoRun() {
      const { phase } = get();
      if (phase !== "ready") return;
      consecutiveFailures = 0;
      set({ phase: "auto_running" });
      autoRunLoop();
    },

    stopAutoRun() {
      if (autoRunTimer) {
        clearTimeout(autoRunTimer);
        autoRunTimer = null;
      }
      if (get().phase === "auto_running") set({ phase: "ready" });
    },

    async injectEvent(eventPrompt: string) {
      const { session } = get();
      if (!session) return;
      try {
        const res = await api.injectEvent(session.session_id, {
          event_prompt: eventPrompt,
        });
        log(
          `Event injected: "${res.event_prompt.substring(0, 60)}..."`,
        );
      } catch (err) {
        const message =
          err instanceof Error ? err.message : String(err);
        log(`Error: ${message}`);
      }
    },

    async createFollowerWithAvatar(name, avatarParams) {
      const { session } = get();
      if (!session) return;

      const apiParams: AvatarParamsResponse = {
        skin_tone: avatarParams.skinTone,
        body_type: avatarParams.bodyType,
        hair_texture: avatarParams.hairTexture,
        hair_style: avatarParams.hairStyle,
        hair_color: avatarParams.hairColor,
        outfit: avatarParams.outfit,
        outfit_color: avatarParams.outfitColor,
        accessories: avatarParams.accessories,
      };

      const res = await api.createFollower(session.session_id, {
        name,
        avatar_params: apiParams,
      });
      log(
        `Joined as "${res.name}" (follower #${res.follower_id})`,
      );

      const followerRes = await api.getFollowers(
        session.session_id,
        0,
        200,
      );
      set({
        followers: followerRes.followers.map(toMapFollower),
      });
    },

    async disconnect() {
      get().stopAutoRun();
      socket?.disconnect();
      socket = null;

      const { session } = get();
      if (session) {
        try {
          await api.pauseSession(session.session_id);
        } catch {
          // best-effort
        }
      }

      set({
        session: null,
        followers: [],
        phase: "idle",
      });
    },

    toggleEventsSheet() {
      set((s) => ({ showEventsSheet: !s.showEventsSheet }));
    },

    toggleAvatarSheet() {
      set((s) => ({ showAvatarSheet: !s.showAvatarSheet }));
    },

    dismissWelcome() {
      set({ showWelcome: false });
    },
  };
});
