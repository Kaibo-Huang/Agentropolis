/**
 * Avatar Creator UI — structure and types.
 *
 * Users create a custom avatar (skin tone, hair, outfit, accessories) and
 * can "Join simulation" to create a new follower with that avatar.
 *
 * Component layout:
 *
 *   AvatarCreator/
 *     AvatarPreview     — live preview (2D/3D) of current params
 *     SkinToneSlider    — 0..1
 *     BodyTypeSelect    — slim | average | broad
 *     HairStyleSelect   — short, long, fade, bun, braids, afro, ponytail
 *     HairTextureSelect — straight, wavy, curly, coily
 *     HairColorPicker   — palette or hex
 *     OutfitSelect      — casual, professional, student, athletic, construction, service
 *     OutfitColorPicker — palette or hex
 *     AccessoriesSelect — multi-select: glasses, hat, bag, scarf
 *     useAvatarParams   — state: AvatarParams; sync to preview
 *     submitCustomAvatar — POST with CustomAvatar (same as AvatarParams)
 *
 * Output: CustomAvatar (same shape as AvatarParams) → API creates follower
 * with avatar_params = payload, avatar_seed = null.
 */

import type { AvatarParams } from "../types/avatar.js";

export const BODY_TYPES: readonly AvatarParams["bodyType"][] = [
  "slim",
  "average",
  "broad",
];

export const HAIR_TEXTURES: readonly AvatarParams["hairTexture"][] = [
  "straight",
  "wavy",
  "curly",
  "coily",
];

export const HAIR_STYLES: readonly AvatarParams["hairStyle"][] = [
  "short",
  "long",
  "fade",
  "bun",
  "braids",
  "afro",
  "ponytail",
];

export const OUTFIT_TYPES: readonly AvatarParams["outfit"][] = [
  "casual",
  "professional",
  "student",
  "athletic",
  "construction",
  "service",
];

export const ACCESSORY_OPTIONS = ["glasses", "hat", "bag", "scarf"] as const;

/** Default params for the creator (neutral starting point). */
export const DEFAULT_AVATAR_PARAMS: AvatarParams = {
  skinTone: 0.4,
  bodyType: "average",
  hairTexture: "straight",
  hairStyle: "short",
  hairColor: "#4a3728",
  outfit: "casual",
  outfitColor: "#2c3e50",
  accessories: [],
};

/**
 * Convert AvatarParams to API shape (snake_case) for POST /sessions/:id/followers
 * with custom avatar.
 */
export function avatarParamsToApi(p: AvatarParams): Record<string, unknown> {
  return {
    skin_tone: p.skinTone,
    body_type: p.bodyType,
    hair_texture: p.hairTexture,
    hair_style: p.hairStyle,
    hair_color: p.hairColor,
    outfit: p.outfit,
    outfit_color: p.outfitColor,
    accessories: p.accessories,
  };
}
