/**
 * Avatar parameter schema — shared with backend.
 * Procedural avatars are generated from a seed; custom avatars store these params.
 * No photos or image uploads.
 */

export type BodyType = "slim" | "average" | "broad";

export type HairTexture = "straight" | "wavy" | "curly" | "coily";

export type HairStyle =
  | "short"
  | "long"
  | "fade"
  | "bun"
  | "braids"
  | "afro"
  | "ponytail";

export type OutfitType =
  | "casual"
  | "professional"
  | "student"
  | "athletic"
  | "construction"
  | "service";

export interface AvatarParams {
  /** 0 = light, 1 = dark; continuous for diversity */
  skinTone: number;
  bodyType: BodyType;
  hairTexture: HairTexture;
  hairStyle: HairStyle;
  /** Hex or palette id */
  hairColor: string;
  outfit: OutfitType;
  /** Hex or palette id */
  outfitColor: string;
  /** e.g. ['glasses', 'bag'] */
  accessories: string[];
}

/** Same shape as AvatarParams; used when user creates custom avatar */
export type CustomAvatar = AvatarParams;

/** Follower payload from API may include avatar fields */
export interface FollowerAvatarData {
  avatarSeed: number | null;
  avatarParams: AvatarParams | null;
}
