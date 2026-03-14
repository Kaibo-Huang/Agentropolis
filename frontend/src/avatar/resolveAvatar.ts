/**
 * Resolve avatar params for a follower.
 * If API sends avatar_params, use them (convert snake_case → camelCase).
 * Else if avatar_seed is set, generate deterministically (must match backend generator).
 */

import type { AvatarParams } from "../types/avatar.js";
import type { AvatarParamsResponse } from "../api/types.js";

const BODY_TYPES = ["slim", "average", "broad"] as const;
const BODY_WEIGHTS = [0.25, 0.5, 0.25];

const HAIR_TEXTURES = ["straight", "wavy", "curly", "coily"] as const;
const HAIR_TEXTURE_WEIGHTS = [0.35, 0.3, 0.22, 0.13];

const HAIR_STYLES = [
  "short",
  "long",
  "fade",
  "bun",
  "braids",
  "afro",
  "ponytail",
] as const;
const HAIR_STYLE_WEIGHTS = [0.22, 0.2, 0.12, 0.14, 0.12, 0.1, 0.1];

const OUTFIT_TYPES = [
  "casual",
  "professional",
  "student",
  "athletic",
  "construction",
  "service",
] as const;
const OUTFIT_WEIGHTS = [0.3, 0.2, 0.15, 0.15, 0.1, 0.1];

const SKIN_PALETTE = [
  "#f5e6d3",
  "#e8d5c4",
  "#d4b896",
  "#c4a574",
  "#a67c52",
  "#8d5524",
  "#6b4423",
  "#5c3d22",
  "#4a3728",
  "#2d1f14",
];

const HAIR_COLORS = [
  "#1a1a1a",
  "#2d2d2d",
  "#4a3728",
  "#5c4033",
  "#6b4423",
  "#8d5524",
  "#a67c52",
  "#c4a574",
  "#d4b896",
  "#e8d5c4",
  "#deb887",
  "#daa520",
  "#b8860b",
  "#8b4513",
  "#654321",
  "#2d1f14",
  "#4a4a4a",
  "#6b6b6b",
  "#8b7355",
];

const OUTFIT_COLORS = [
  "#2c3e50",
  "#34495e",
  "#7f8c8d",
  "#95a5a6",
  "#bdc3c7",
  "#e74c3c",
  "#c0392b",
  "#e67e22",
  "#d35400",
  "#f39c12",
  "#27ae60",
  "#16a085",
  "#2980b9",
  "#3498db",
  "#9b59b6",
  "#8e44ad",
  "#1abc9c",
  "#f1c40f",
  "#ecf0f1",
];

const ACCESSORY_OPTIONS = ["glasses", "hat", "bag", "scarf"];
const ACCESSORY_PROBABILITY = 0.35;

/** Mulberry32: same as backend so same seed → same params */
function nextSeed(seed: number): number {
  return ((seed + 0x6d2b79f5) | 0) >>> 0;
}

function random(seed: number): { u: number; next: number } {
  const next = nextSeed(seed);
  const u = next / 0xffffffff;
  return { u, next };
}

function randint(seed: number, lo: number, hi: number): { value: number; next: number } {
  const { u, next } = random(seed);
  const value = lo + Math.floor(u * (hi - lo + 1)) % (hi - lo + 1);
  return { value, next };
}

function choice<T>(
  seed: number,
  items: readonly T[],
  weights?: number[]
): { value: T; next: number } {
  if (!weights) {
    const { value, next } = randint(seed, 0, items.length - 1);
    return { value: items[value], next };
  }
  const { u, next } = random(seed);
  let r = u * weights.reduce((a, b) => a + b, 0);
  for (let i = 0; i < items.length; i++) {
    r -= weights[i];
    if (r <= 0) return { value: items[i], next };
  }
  return { value: items[items.length - 1], next };
}

/** Generate AvatarParams from seed; must match backend generator. */
export function generateAvatarFromSeed(seed: number): AvatarParams {
  let s = (seed >>> 0) || 1;

  const r1 = random(s);
  s = r1.next;
  const r2 = random(s);
  s = r2.next;
  let t = (r1.u + r2.u) / 2;
  t = Math.max(0, Math.min(1, t));
  const idx = Math.max(
    0,
    Math.min(SKIN_PALETTE.length - 1, Math.round(t * (SKIN_PALETTE.length - 1)))
  );
  const skinHex = SKIN_PALETTE[idx];

  const body = choice(s, BODY_TYPES, BODY_WEIGHTS);
  s = body.next;
  const hairTex = choice(s, HAIR_TEXTURES, HAIR_TEXTURE_WEIGHTS);
  s = hairTex.next;
  const hairStyle = choice(s, HAIR_STYLES, HAIR_STYLE_WEIGHTS);
  s = hairStyle.next;
  const hairColor = choice(s, HAIR_COLORS, undefined);
  s = hairColor.next;
  const outfit = choice(s, OUTFIT_TYPES, OUTFIT_WEIGHTS);
  s = outfit.next;
  const outfitColor = choice(s, OUTFIT_COLORS, undefined);
  s = outfitColor.next;

  const accessories: string[] = [];
  for (const opt of ACCESSORY_OPTIONS) {
    const { u, next } = random(s);
    s = next;
    if (u < ACCESSORY_PROBABILITY) accessories.push(opt);
  }

  return {
    skinTone: t,
    bodyType: body.value,
    hairTexture: hairTex.value,
    hairStyle: hairStyle.value,
    hairColor: hairColor.value,
    outfit: outfit.value,
    outfitColor: outfitColor.value,
    accessories,
  };
}

/** Convert API snake_case avatar params to frontend camelCase AvatarParams */
export function avatarParamsFromApi(api: AvatarParamsResponse): AvatarParams {
  return {
    skinTone: api.skin_tone,
    bodyType: api.body_type as AvatarParams["bodyType"],
    hairTexture: api.hair_texture as AvatarParams["hairTexture"],
    hairStyle: api.hair_style as AvatarParams["hairStyle"],
    hairColor: api.hair_color,
    outfit: api.outfit as AvatarParams["outfit"],
    outfitColor: api.outfit_color,
    accessories: api.accessories ?? [],
  };
}

/**
 * Resolve final AvatarParams for a follower.
 * Prefer avatar_params from API; else generate from avatar_seed.
 */
export function resolveAvatar(
  avatarSeed: number | null,
  avatarParams: AvatarParamsResponse | null
): AvatarParams | null {
  if (avatarParams != null) return avatarParamsFromApi(avatarParams);
  if (avatarSeed != null) return generateAvatarFromSeed(avatarSeed);
  return null;
}
