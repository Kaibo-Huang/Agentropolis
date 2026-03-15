import { create } from "zustand";
import { ApiClient } from "../api/client";
import { SimulationSocket } from "../api/client";
import type {
  SessionResponse,
  ArchetypeResponse,
  PostResponse,
  AvatarParamsResponse,
  TickResponse,
  WsFollowerUpdate,
  WsPostUpdate,
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
    industry: f.industry,
    position: toMapbox(f.position),
    happiness: f.happiness,
    recent_memories: (f.recent_memories ?? []).map((m) => ({
      virtual_time: m.virtual_time,
      action_type: m.action_type,
      thinking: m.thinking,
    })),
    age: f.age,
    gender: f.gender,
    race: f.race,
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

interface PrefetchedTick {
  sessionId: string;
  tickResponse: TickResponse;
  followers: FollowerResponse[];
  posts: PostResponse[];
  session: SessionResponse;
  prefetchedAt: number;
}
export type ToolkitTab =
  | "latest_posts"
  | "demographics"
  | "archetypes"
  | "event_log"
  | "inject_event"
  | "create_avatar";

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
  activeToolkitTab: ToolkitTab;
  isToolkitOpenMobile: boolean;

  // Actions
  createAndConnect: (prompt?: string) => Promise<void>;
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
  setToolkitTab: (tab: ToolkitTab) => void;
  toggleToolkitMobile: () => void;
  openToolkitTab: (tab: ToolkitTab) => void;
  dismissWelcome: () => void;
  log: (msg: string) => void;
}

// ── Store ──

const API_BASE =
  (typeof process !== "undefined" &&
    process.env.NEXT_PUBLIC_API_URL) ||
  "http://localhost:8000";
const WS_BASE = API_BASE.replace(/^http/, "ws");

const PREFETCH_KEY = "agentropolis_prefetched_tick";

// Closure state (not serializable, not part of React state)
let api: ApiClient = new ApiClient(API_BASE);
let socket: SimulationSocket | null = null;
let autoRunTimer: ReturnType<typeof setTimeout> | null = null;
let ticking = false;
let consecutiveFailures = 0;
let prefetching = false;
let pendingPrefetchResolvers: Array<() => void> = [];
let wsTickUpdateCount = 0;
let liveTickActive = false;

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

  function readPrefetchCache(sessionId: string): PrefetchedTick | null {
    try {
      if (typeof localStorage === "undefined") return null;
      const raw = localStorage.getItem(PREFETCH_KEY);
      if (!raw) return null;
      const entry: PrefetchedTick = JSON.parse(raw);
      if (entry.sessionId !== sessionId) return null;
      if (Date.now() - entry.prefetchedAt > 60_000) {
        localStorage.removeItem(PREFETCH_KEY);
        return null;
      }
      return entry;
    } catch {
      return null;
    }
  }

  function writePrefetchCache(data: PrefetchedTick): void {
    try {
      if (typeof localStorage === "undefined") return;
      localStorage.setItem(PREFETCH_KEY, JSON.stringify(data));
    } catch {
      // quota error — ignore
    }
  }

  function clearPrefetchCache(): void {
    try {
      if (typeof localStorage === "undefined") return;
      localStorage.removeItem(PREFETCH_KEY);
    } catch {}
  }

  async function preprocessNextTick(): Promise<void> {
    if (prefetching) return;
    const { session } = get();
    if (!session) return;
    prefetching = true;
    try {
      const currentVt = new Date(session.virtual_time);
      const targetVt = new Date(currentVt.getTime() + 3_600_000);

      // Tick first (mutates server state), then fetch updated data
      const tickResponse = await api.tick(session.session_id, {
        target_time: targetVt.toISOString(),
      });
      const [sessionRes, followerRes, postRes] = await Promise.all([
        api.getSession(session.session_id),
        api.getFollowers(session.session_id, 0, 1000),
        api.getPosts(session.session_id, 0, 20),
      ]);

      writePrefetchCache({
        sessionId: session.session_id,
        tickResponse,
        followers: followerRes.followers,
        posts: postRes.posts,
        session: sessionRes,
        prefetchedAt: Date.now(),
      });
    } catch {
      clearPrefetchCache();
    } finally {
      prefetching = false;
      const resolvers = pendingPrefetchResolvers.splice(0);
      resolvers.forEach((r) => r());
    }
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
    activeToolkitTab: "latest_posts",
    isToolkitOpenMobile: false,

    // Actions
    log,

    async createAndConnect(prompt?: string) {
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
              const data = msg.data as { message?: string };
              log(`WS error: ${data?.message ?? "unknown"}`);
            } else if (msg.type === "tick_start") {
              const data = msg.data as { tick_number: number; archetype_count: number };
              log(`Tick #${data.tick_number} started — ${data.archetype_count} archetypes`);
            } else if (msg.type === "tick_archetype_update") {
              if (!liveTickActive) return;
              const data = msg.data as {
                archetype_id: number;
                followers: WsFollowerUpdate[];
                posts: WsPostUpdate[];
              };
              wsTickUpdateCount++;

              if (data.followers.length > 0) {
                const updates = new Map(data.followers.map((f) => [f.follower_id, f]));
                set((s) => ({
                  followers: s.followers.map((f) => {
                    const u = updates.get(f.follower_id);
                    if (!u) return f;
                    return {
                      ...f,
                      happiness: u.happiness,
                      position: u.position
                        ? toMapbox(u.position as [number, number])
                        : f.position,
                    };
                  }),
                }));
              }

              if (data.posts.length > 0) {
                const newPosts: PostResponse[] = data.posts.map((p) => ({
                  post_id: p.post_id,
                  follower_id: p.follower_id,
                  text: p.text,
                  virtual_time: p.virtual_time,
                  created_at: null as unknown as string,
                }));
                set((s) => ({
                  posts: [...newPosts, ...s.posts].slice(0, 100),
                }));
              }
            } else if (msg.type === "tick_complete") {
              if (!liveTickActive) return;
              const data = msg.data as {
                tick_number: number;
                virtual_time: string;
                archetypes_processed: number;
                archetypes_failed: number;
              };
              set((s) => {
                if (!s.session) return {};
                const updatedSession = { ...s.session, virtual_time: data.virtual_time };
                return {
                  session: updatedSession,
                  hourOfDay: computeHourOfDay(updatedSession),
                };
              });
              log(`Tick #${data.tick_number} complete — ${data.archetypes_processed} OK, ${data.archetypes_failed} fail`);
            }
          },
          (state) => log(`WS: ${state}`),
        );
        socket.connect();

        // 4. Fetch initial data in parallel
        const [followerRes, archetypeRes, postRes] = await Promise.all([
          api.getFollowers(session.session_id, 0, 1000),
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

        // Inject the user's simulation prompt as the first event
        if (prompt) {
          try {
            await api.injectEvent(session.session_id, { event_prompt: prompt });
            log(`Event injected: "${prompt.substring(0, 60)}${prompt.length > 60 ? "..." : ""}"`);
          } catch (err) {
            const message = err instanceof Error ? err.message : String(err);
            log(`Event injection failed: ${message}`);
          }
        }
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
        // --- Live tick (streaming via WS) ---
        clearPrefetchCache();
        const currentVt = new Date(session.virtual_time);
        const targetVt = new Date(currentVt.getTime() + 3_600_000);

        wsTickUpdateCount = 0;
        liveTickActive = true;

        const tickResult = await api.tick(session.session_id, {
          target_time: targetVt.toISOString(),
        });

        liveTickActive = false;

        // If WS streamed incremental updates, followers/posts are already
        // current for movement/happiness/posts. Refresh followers anyway so
        // popup fields like recent memories stay in sync.
        if (wsTickUpdateCount > 0) {
          const [sessionRes, followerRes] = await Promise.all([
            api.getSession(session.session_id),
            api.getFollowers(session.session_id, 0, 1000),
          ]);
          set({
            session: sessionRes,
            followers: followerRes.followers.map(toMapFollower),
            hourOfDay: computeHourOfDay(sessionRes),
          });
        } else {
          const [sessionRes, followerRes, postRes] = await Promise.all([
            api.getSession(session.session_id),
            api.getFollowers(session.session_id, 0, 1000),
            api.getPosts(session.session_id, 0, 20),
          ]);
          set({
            session: sessionRes,
            followers: followerRes.followers.map(toMapFollower),
            posts: postRes.posts,
            hourOfDay: computeHourOfDay(sessionRes),
          });
        }

        const { session: updatedSession } = get();
        const vtDisplay = new Date(
          updatedSession!.virtual_time,
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
        liveTickActive = false;
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
        // Build effects summary for user feedback
        const fx = res.effects;
        if (fx) {
          const parts: string[] = [];
          if (fx.stay_home_rate != null) parts.push(`${Math.round((fx.stay_home_rate as number) * 100)}% stay home`);
          if (fx.happiness_delta != null) parts.push(`happiness ${(fx.happiness_delta as number) > 0 ? "+" : ""}${fx.happiness_delta}`);
          if (fx.tweet_rate_multiplier != null) parts.push(`tweets ${fx.tweet_rate_multiplier}x`);
          if (fx.disease_transmission_multiplier != null) parts.push(`disease ${fx.disease_transmission_multiplier}x`);
          if (fx.tweet_sentiment) parts.push(`mood: ${fx.tweet_sentiment}`);
          const summary = parts.length > 0 ? parts.join(", ") : "narrative-only";
          log(`Event injected: ${summary}`);
        } else {
          log(`Event injected: "${res.event_prompt.substring(0, 60)}..."`);
        }
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
        1000,
      );
      set({
        followers: followerRes.followers.map(toMapFollower),
      });
    },

    async disconnect() {
      clearPrefetchCache();
      prefetching = false;
      pendingPrefetchResolvers = [];

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

    setToolkitTab(tab) {
      set({ activeToolkitTab: tab });
    },

    toggleToolkitMobile() {
      set((s) => ({ isToolkitOpenMobile: !s.isToolkitOpenMobile }));
    },

    openToolkitTab(tab) {
      set({
        activeToolkitTab: tab,
        isToolkitOpenMobile: true,
      });
    },

    dismissWelcome() {
      set({ showWelcome: false });
    },
  };
});
