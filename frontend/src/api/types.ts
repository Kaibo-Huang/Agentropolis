// ── Session ──

export interface SessionConfig {
  total_population: number;
  archetype_count: number;
  company_count: number;
}

export interface SessionResponse {
  session_id: string;
  created_at: string;
  virtual_time: string;
  status: "paused" | "running";
  config: SessionConfig | null;
  follower_count: number;
}

// ── Tick ──

export interface TickRequest {
  target_time: string; // ISO 8601
}

export interface TickResponse {
  tick_number: number;
  virtual_time: string;
  archetypes_processed: number;
  archetypes_failed: number;
}

// ── Followers ──

export interface FollowerResponse {
  follower_id: number;
  archetype_id: number;
  name: string;
  age: number | null;
  gender: string | null;
  race: string | null;
  home_position: [number, number] | null;
  work_position: [number, number] | null;
  position: [number, number] | null;
  status_ailments: string[] | null;
  happiness: number;
  volatility: number;
  /** Present after avatar migration; used to resolve avatar for rendering */
  avatar_seed?: number | null;
  avatar_params?: AvatarParamsResponse | null;
}

/** Avatar params as returned by API (snake_case) */
export interface AvatarParamsResponse {
  skin_tone: number;
  body_type: string;
  hair_texture: string;
  hair_style: string;
  hair_color: string;
  outfit: string;
  outfit_color: string;
  accessories: string[];
}

export interface FollowerListResponse {
  followers: FollowerResponse[];
  total: number;
  offset: number;
  limit: number;
}

// ── Archetypes ──

export interface ArchetypeResponse {
  archetype_id: number;
  industry: string;
  social_class: string | null;
  region: string;
  follower_count: number;
}

export interface ArchetypeListResponse {
  archetypes: ArchetypeResponse[];
}

// ── Events ──

export interface InjectEventRequest {
  event_prompt: string;
  virtual_time?: string;
}

export interface EventResponse {
  event_id: number;
  event_prompt: string;
  virtual_time: string;
  session_id: string;
}

// ── Posts ──

export interface PostResponse {
  post_id: number;
  follower_id: number;
  text: string;
  virtual_time: string;
  created_at: string | null;
}

export interface PostListResponse {
  posts: PostResponse[];
  offset: number;
  limit: number;
}

// ── WebSocket ──

export type WsOutgoing = { type: "subscribe" } | { type: "pong" };

export type WsIncoming =
  | { type: "subscribed"; data: { session_id: string } }
  | { type: "ping" }
  | { type: "error"; data: { message: string } };

// Mapbox [lng, lat] tuple (backend stores [lat, lng])
export type LngLat = [number, number];
