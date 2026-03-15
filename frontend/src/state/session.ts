import { ApiClient } from "../api/client.js";
import { SimulationSocket } from "../api/client.js";
import type {
  SessionResponse,
  TickResponse,
  FollowerResponse,
  ArchetypeResponse,
  PostResponse,
  LngLat,
  WsFollowerUpdate,
  WsPostUpdate,
  WsArchetypeAction,
} from "../api/types.js";
import type { MapFollower } from "../world/toronto-mapbox.js";
import { resolveAvatar } from "../avatar/resolveAvatar.js";

/** Convert backend [lat, lng] to Mapbox [lng, lat]. */
export function toMapbox(backendPos: [number, number] | null): LngLat | null {
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

export type ControllerPhase =
  | "idle"
  | "loading"
  | "ready"
  | "ticking"
  | "auto_running"
  | "error";

export interface SessionControllerCallbacks {
  onPhaseChange(phase: ControllerPhase): void;
  onSessionUpdate(session: SessionResponse): void;
  onFollowersUpdate(followers: MapFollower[]): void;
  onArchetypesUpdate(archetypes: ArchetypeResponse[]): void;
  onPostsUpdate(posts: PostResponse[]): void;
  onTickComplete(tick: TickResponse): void;
  onArchetypeDecision?(archetypeId: number, actions: WsArchetypeAction[]): void;
  onError(err: Error): void;
  onLog(msg: string): void;
}

export class SessionController {
  private api: ApiClient;
  private socket: SimulationSocket | null = null;
  private session: SessionResponse | null = null;
  private followers: MapFollower[] = [];
  private archetypes: ArchetypeResponse[] = [];
  private posts: PostResponse[] = [];
  private autoRunTimer: ReturnType<typeof setTimeout> | null = null;
  private phase: ControllerPhase = "idle";
  private _wsTickUpdateCount = 0;

  constructor(
    private apiBaseUrl: string,
    private wsBaseUrl: string,
    private cb: SessionControllerCallbacks,
  ) {
    this.api = new ApiClient(apiBaseUrl);
  }

  // ── Getters ──

  getPhase(): ControllerPhase {
    return this.phase;
  }

  getSession(): SessionResponse | null {
    return this.session;
  }

  getFollowers(): MapFollower[] {
    return this.followers;
  }

  getVirtualTime(): Date | null {
    return this.session ? new Date(this.session.virtual_time) : null;
  }

  /** Returns the UTC hour (0-23) from virtual_time, for day/night cycle. */
  getHourOfDay(): number {
    const vt = this.getVirtualTime();
    return vt ? vt.getUTCHours() : 8;
  }

  // ── Lifecycle ──

  async createAndConnect(): Promise<void> {
    this.setPhase("loading");
    try {
      // 1. Create session
      this.session = await this.api.createSession();
      this.cb.onSessionUpdate(this.session);
      this.cb.onLog(
        `Session created: ${this.session.session_id.substring(0, 8)}...`,
      );

      // 2. Resume (paused -> running)
      this.session = await this.api.resumeSession(this.session.session_id);
      this.cb.onSessionUpdate(this.session);

      // 3. Connect WebSocket
      this.socket = new SimulationSocket(
        this.wsBaseUrl,
        this.session.session_id,
        (msg) => this.handleWsMessage(msg),
        (state) => this.cb.onLog(`WS: ${state}`),
      );
      this.socket.connect();

      // 4. Fetch initial data in parallel
      const [followerRes, archetypeRes, postRes] = await Promise.all([
        this.api.getFollowers(this.session.session_id, 0, 200),
        this.api.getArchetypes(this.session.session_id),
        this.api.getPosts(this.session.session_id, 0, 20),
      ]);

      this.followers = followerRes.followers.map(toMapFollower);
      this.archetypes = archetypeRes.archetypes;
      this.posts = postRes.posts;

      this.cb.onFollowersUpdate(this.followers);
      this.cb.onArchetypesUpdate(this.archetypes);
      this.cb.onPostsUpdate(this.posts);
      this.cb.onLog(
        `Ready: ${this.followers.length} followers, ${this.archetypes.length} archetypes`,
      );

      this.setPhase("ready");
    } catch (err) {
      this.setPhase("error");
      this.cb.onError(err instanceof Error ? err : new Error(String(err)));
    }
  }

  async tickOnce(): Promise<void> {
    if (
      !this.session ||
      (this.phase !== "ready" && this.phase !== "auto_running")
    )
      return;

    const prevPhase = this.phase;
    if (prevPhase === "ready") this.setPhase("ticking");

    try {
      // Compute target_time = current virtual_time + 1 hour
      const currentVt = new Date(this.session.virtual_time);
      const targetVt = new Date(currentVt.getTime() + 3_600_000);

      this._wsTickUpdateCount = 0;
      const tickResult = await this.api.tick(this.session.session_id, {
        target_time: targetVt.toISOString(),
      });
      this.cb.onTickComplete(tickResult);

      // If WS streamed incremental updates during the tick, followers and posts
      // are already current — only refresh session state (for virtual_time).
      // Otherwise do the full refresh as a fallback.
      if (this._wsTickUpdateCount > 0) {
        const sessionRes = await this.api.getSession(this.session.session_id);
        this.session = sessionRes;
        this.cb.onSessionUpdate(this.session);
      } else {
        const [sessionRes, followerRes, postRes] = await Promise.all([
          this.api.getSession(this.session.session_id),
          this.api.getFollowers(this.session.session_id, 0, 200),
          this.api.getPosts(this.session.session_id, 0, 20),
        ]);
        this.session = sessionRes;
        this.followers = followerRes.followers.map(toMapFollower);
        this.posts = postRes.posts;
        this.cb.onFollowersUpdate(this.followers);
        this.cb.onPostsUpdate(this.posts);
      }

      const vtDisplay = new Date(this.session.virtual_time).toLocaleString();
      this.cb.onLog(
        `Tick ${tickResult.tick_number}: ${vtDisplay} (${tickResult.archetypes_processed} OK, ${tickResult.archetypes_failed} fail)`,
      );

      if (prevPhase === "ready") this.setPhase("ready");
      else if (prevPhase === "auto_running") this.setPhase("auto_running");
    } catch (err) {
      this.cb.onError(err instanceof Error ? err : new Error(String(err)));
      if (prevPhase === "ready") this.setPhase("ready");
      else if (prevPhase === "auto_running") this.setPhase("auto_running");
    }
  }

  startAutoRun(): void {
    if (this.phase !== "ready" && this.phase !== "auto_running") return;
    if (this.phase === "auto_running") return;
    this.setPhase("auto_running");
    this.autoRunLoop();
  }

  stopAutoRun(): void {
    if (this.autoRunTimer) {
      clearTimeout(this.autoRunTimer);
      this.autoRunTimer = null;
    }
    if (this.phase === "auto_running") this.setPhase("ready");
  }

  async injectEvent(eventPrompt: string): Promise<void> {
    if (!this.session) return;
    try {
      const res = await this.api.injectEvent(this.session.session_id, {
        event_prompt: eventPrompt,
      });
      this.cb.onLog(
        `Event injected: "${res.event_prompt.substring(0, 60)}..."`,
      );
    } catch (err) {
      this.cb.onError(err instanceof Error ? err : new Error(String(err)));
    }
  }

  /** Create a follower with custom avatar and refresh list. */
  async createFollowerWithAvatar(
    name: string,
    avatarParams: {
      skinTone: number;
      bodyType: string;
      hairTexture: string;
      hairStyle: string;
      hairColor: string;
      outfit: string;
      outfitColor: string;
      accessories: string[];
    },
  ): Promise<void> {
    if (!this.session) return;
    const res = await this.api.createFollower(this.session.session_id, {
      name,
      avatar_params: {
        skin_tone: avatarParams.skinTone,
        body_type: avatarParams.bodyType,
        hair_texture: avatarParams.hairTexture,
        hair_style: avatarParams.hairStyle,
        hair_color: avatarParams.hairColor,
        outfit: avatarParams.outfit,
        outfit_color: avatarParams.outfitColor,
        accessories: avatarParams.accessories,
      },
    });
    this.cb.onLog(`Joined as "${res.name}" (follower #${res.follower_id})`);
    const followerRes = await this.api.getFollowers(this.session.session_id, 0, 200);
    this.followers = followerRes.followers.map(toMapFollower);
    this.cb.onFollowersUpdate(this.followers);
  }

  async disconnect(): Promise<void> {
    this.stopAutoRun();
    this.socket?.disconnect();
    this.socket = null;
    if (this.session) {
      try {
        await this.api.pauseSession(this.session.session_id);
      } catch {
        /* best-effort */
      }
    }
    this.session = null;
    this.followers = [];
    this.setPhase("idle");
  }

  // ── Private ──

  private setPhase(p: ControllerPhase): void {
    this.phase = p;
    this.cb.onPhaseChange(p);
  }

  private handleWsMessage(msg: { type: string; data?: unknown }): void {
    if (msg.type === "subscribed") {
      this.cb.onLog("WebSocket subscribed");
    } else if (msg.type === "error") {
      const data = msg.data as { message?: string } | undefined;
      this.cb.onLog(`WS error: ${data?.message ?? "unknown"}`);
    } else if (msg.type === "tick_start") {
      const data = msg.data as { tick_number: number; virtual_time: string; archetype_count: number };
      this.cb.onLog(`Tick #${data.tick_number} started — ${data.archetype_count} archetypes`);
    } else if (msg.type === "tick_archetype_decision") {
      const data = msg.data as { archetype_id: number; actions: WsArchetypeAction[] };
      this.cb.onArchetypeDecision?.(data.archetype_id, data.actions);
    } else if (msg.type === "tick_archetype_update") {
      const data = msg.data as { archetype_id: number; followers: WsFollowerUpdate[]; posts: WsPostUpdate[] };
      this._wsTickUpdateCount++;

      // Merge follower happiness and position updates in-place
      if (data.followers.length > 0) {
        const updates = new Map(data.followers.map((f) => [f.follower_id, f]));
        this.followers = this.followers.map((f) => {
          const u = updates.get(f.follower_id);
          if (!u) return f;
          return {
            ...f,
            happiness: u.happiness,
            position: u.position ? toMapbox(u.position as [number, number]) : f.position,
          };
        });
        this.cb.onFollowersUpdate(this.followers);
      }

      // Prepend new posts (keep last 100)
      if (data.posts.length > 0) {
        const newPosts = data.posts.map((p) => ({
          post_id: p.post_id,
          follower_id: p.follower_id,
          text: p.text,
          virtual_time: p.virtual_time,
          created_at: null,
        }));
        this.posts = [...newPosts, ...this.posts].slice(0, 100);
        this.cb.onPostsUpdate(this.posts);
      }
    } else if (msg.type === "tick_complete") {
      const data = msg.data as { tick_number: number; virtual_time: string; archetypes_processed: number; archetypes_failed: number };
      // Update virtual time immediately so the clock advances before HTTP response
      if (this.session) {
        this.session = { ...this.session, virtual_time: data.virtual_time };
        this.cb.onSessionUpdate(this.session);
      }
      this.cb.onLog(`Tick #${data.tick_number} complete — ${data.archetypes_processed} OK, ${data.archetypes_failed} fail`);
    }
  }

  private async autoRunLoop(): Promise<void> {
    if (this.phase !== "auto_running") return;
    await this.tickOnce();
    if (this.phase !== "auto_running") return;
    this.autoRunTimer = setTimeout(() => this.autoRunLoop(), 2000);
  }
}
