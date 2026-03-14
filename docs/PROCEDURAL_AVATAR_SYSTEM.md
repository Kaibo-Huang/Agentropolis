# Procedural Avatar System — Design

Replace circle agents with simple stylized human avatars that support multicultural diversity, user-created custom avatars, and efficient rendering for 10,000+ characters. No photos or image uploads.

---

## 1. Avatar Generation Algorithm

### 1.1 Deterministic seed → parameters

Every agent has an **avatar seed** (e.g. 32-bit integer). The same seed always produces the same avatar.

```
avatar_params = generate_avatar_from_seed(seed)
```

**Algorithm:**

1. Initialize a PRNG with the seed (e.g. mulberry32, xoshiro128**, or a simple seeded hash).
2. Sample each dimension from continuous or discrete distributions:
   - **skin_tone**: `random() → [0, 1]` (0 = light, 1 = dark).
   - **body_type**: discrete choice from `["slim", "average", "broad"]` with weights.
   - **hair_texture**: `["straight", "wavy", "curly", "coily"]` (weighted).
   - **hair_style**: `["short", "long", "fade", "bun", "braids", "afro", "ponytail"]` (can be influenced by hair_texture for coherence).
   - **hair_color**: sample from a palette (natural + fashion colors) or HSV with constrained H.
   - **outfit**: `["casual", "professional", "student", "athletic", "construction", "service"]`; optionally biased by **archetype industry/social_class** (e.g. Finance → more professional).
   - **outfit_color**: sample from a palette per outfit type.
   - **accessories**: small set of slots (e.g. hat, glasses, bag) each with probability and variant from PRNG.

3. Optional: **bias by archetype** when generating for a follower:
   - Use `(seed, archetype_id, follower_id)` so same archetype can have similar outfit style while individuals still vary.
   - Industry → outfit type weights; social_class → outfit formality.

### 1.2 Multicultural diversity (continuous, no hard-coded races)

- **Skin tone**: Single continuous `[0, 1]` mapped to a gradient (e.g. from a 6–10 step palette). No labels; visual only.
- **Hair texture**: Four types (straight, wavy, curly, coily) with weighted sampling so the population mix is diverse.
- **Hair styles**: Multiple options that work across textures (short, long, bun, braids, afro, ponytail, fade).
- **Clothing**: Varied by industry/region/social class and random choice so the crowd looks mixed.

Weights for hair texture and skin tone can be tuned to reflect Toronto demographics without storing or displaying race categories; the avatar is just parameters.

### 1.3 User-created avatars

User choices are stored **explicitly** (not derived from a seed):

- **CustomAvatar**: `{ skinTone, bodyType, hairStyle, hairColor, outfit, accessories[] }`
- Backend can store either:
  - **avatar_seed** (null for custom) + **avatar_params** (JSON), or
  - **avatar_seed** for procedurals, and for custom a dedicated “custom_avatar” JSON or columns.

Same parameter schema as generated avatars so the renderer is identical.

---

## 2. Modular Asset System

### 2.1 Principle

- **One shared base body** (low-poly, rigged or simple hierarchy).
- **Modular hair meshes** (one mesh per hair style; optionally per texture variant or use vertex color / texture for variation).
- **Modular clothing meshes** (one mesh per outfit type; color via uniform or vertex color).
- **Accessories**: one mesh per type (hat, glasses, bag); optional per-variant.

No unique meshes per character: only combinations of shared parts + parameters (colors, which parts).

### 2.2 Asset catalog (data-driven)

```ts
// Example: asset registry
interface AvatarAssetCatalog {
  body: { meshId: string; variants: ['slim', 'average', 'broad'] };
  hair: { [styleId: string]: { meshId: string; textures?: string[] } };
  outfits: { [outfitId: string]: { meshId: string; colorRegions: string[] } };
  accessories: { [slot: string]: { meshIds: string[] } };
}
```

- **Body**: single mesh with 3 body type scales or 3 very low-poly meshes.
- **Hair**: e.g. `short`, `long`, `fade`, `bun`, `braids`, `afro`, `ponytail`; hair_color applied as tint or second UV.
- **Outfits**: e.g. `casual`, `professional`, etc.; outfit_color applied to color regions.
- **Accessories**: list of small meshes; each slot (hat, glasses, bag) has 0 or 1 active with variant index.

### 2.3 LOD (Level of Detail)

- **High (close)**: full modular set (body + hair + outfit + accessories).
- **Medium**: same meshes, simplified materials or reduced accessories.
- **Low (far, 10k+)**: billboard sprite or single very low-poly silhouette, color from avatar params (e.g. average of outfit + skin).

---

## 3. Avatar Parameter Schema

### 3.1 Core schema (backend + frontend)

```ts
// Shared TypeScript/Pydantic-style schema

type BodyType = 'slim' | 'average' | 'broad';
type HairTexture = 'straight' | 'wavy' | 'curly' | 'coily';
type HairStyle = 'short' | 'long' | 'fade' | 'bun' | 'braids' | 'afro' | 'ponytail';
type OutfitType = 'casual' | 'professional' | 'student' | 'athletic' | 'construction' | 'service';

interface AvatarParams {
  skinTone: number;           // [0, 1]
  bodyType: BodyType;
  hairTexture: HairTexture;
  hairStyle: HairStyle;
  hairColor: string;          // hex or palette id
  outfit: OutfitType;
  outfitColor: string;        // hex or palette id
  accessories: string[];      // e.g. ['glasses', 'bag'] or ['hat_snapback']
}
```

### 3.2 Stored in DB (per follower)

- **avatar_seed** (nullable int): if set, avatar is generated from seed; deterministic.
- **avatar_params** (JSONB, nullable): if set (e.g. custom avatar), use directly; else derive from avatar_seed.

So: `resolve_avatar(follower) → AvatarParams` = `follower.avatar_params ?? generate_avatar_from_seed(follower.avatar_seed)`.

### 3.3 API

- **GET /sessions/{id}/followers**: include `avatar_seed` and optionally `avatar_params` in each follower.
- **POST /sessions/{id}/followers** (custom avatar): accept `avatar_params` and set `avatar_seed = null` for that follower.

---

## 4. Rendering Pipeline for Thousands of Characters

### 4.1 Goals

- 10,000+ characters on screen.
- Low GPU overhead: shared meshes, instancing, minimal draw calls.
- Same avatar params drive appearance (no unique models per person).

### 4.2 Strategy

1. **GPU instancing**
   - One draw call per (mesh, material) with an instance buffer.
   - Instance attributes: world matrix (or position + rotation + scale), skin_tone, hair_color, outfit_color, and indices for hair style, outfit type, body type, accessories.

2. **Batching**
   - Batch by mesh + material (e.g. body, hair_short, hair_long, …, outfit_casual, …).
   - Each batch: N instances with per-instance uniforms or vertex attributes (depending on engine).

3. **Mapbox integration**
   - Mapbox GL renders the map; agents are either:
     - **Option A**: Mapbox custom layer (CustomLayerInterface) drawing in WebGL with instanced meshes and shared resources; read positions from a GeoJSON source and instance buffer from avatar params.
     - **Option B**: Separate Three.js (or raw WebGL) canvas overlaid and synced to map (lat/lng → world position using map projection). Three.js InstancedMesh is ideal here.

4. **Culling and LOD**
   - Frustum culling: only submit instances in view.
   - Distance LOD: beyond threshold, swap to billboard or single low-poly blob; reduce instance count for far-away agents.

5. **Animation**
   - Single shared walk cycle (skeletal or simple hierarchy).
   - Per-instance: phase offset (from follower_id or position) so not all in sync.
   - No unique animations per character; one walk cycle, many instances.

### 4.3 Data flow

- Backend sends followers with `position`, `avatar_seed` / `avatar_params`.
- Frontend:
  - Resolves `AvatarParams` for each follower (from seed or params).
  - Updates instance buffers: position (from map projection), rotation (e.g. facing movement or north), and per-instance avatar params (colors, variant indices).
  - Each frame: update positions from simulation, update instance buffer, submit instanced draws.

---

## 5. Avatar Creator UI Structure

### 5.1 Purpose

Let users create a custom avatar and insert themselves into the simulation (new follower with custom avatar).

### 5.2 Screens / sections

1. **Preview**
   - Live 3D or 2D preview of the avatar with current choices (same rendering as in-map, or simplified 2D representation).

2. **Controls**
   - **Skin tone**: slider 0–1 (or discrete palette swatches).
   - **Body type**: radio or buttons (slim / average / broad).
   - **Hair**: style dropdown, texture dropdown, color picker or palette.
   - **Outfit**: type dropdown, color picker or palette.
   - **Accessories**: multi-select or toggles (hat, glasses, bag, etc.).

3. **Output**
   - “Join simulation” submits `CustomAvatar` (same shape as `AvatarParams`) to API; backend creates a follower with `avatar_params = payload`, `avatar_seed = null`.

### 5.3 Component structure (example)

```
AvatarCreator/
  AvatarPreview.tsx      — preview canvas or component
  SkinToneSlider.tsx
  HairStyleSelect.tsx
  HairColorPicker.tsx
  OutfitSelect.tsx
  AccessoriesSelect.tsx
  useAvatarParams.ts     — state: AvatarParams; sync to preview
  submitCustomAvatar()   — API call with AvatarParams
```

Preview and in-map renderer both consume `AvatarParams` so appearance is consistent.

---

## 6. Performance Optimizations

| Area | Optimization |
|------|--------------|
| **Instancing** | Single mesh per part (body, hair style, outfit), many instances; one draw call per mesh type. |
| **Culling** | Frustum culling; optional spatial hash for visible set. |
| **LOD** | Beyond N meters: billboard or single quad with dominant color; reduce mesh complexity. |
| **Animation** | One skeleton, one walk cycle; phase offset per instance (no per-agent animation state beyond phase). |
| **Memory** | No per-agent mesh; only per-agent instance data (matrix + a few floats/ints). |
| **Batching** | Sort by mesh/material to minimize state changes. |
| **Seeding** | Resolve avatar params once when follower list updates; cache by follower_id; only recompute on new/updated followers. |

---

## 7. Walking Animation

- **Approach**: One looping walk cycle, reused for all.
- **Options**:
  - **Skeletal**: shared rig, one walk animation; instances drive only transform + animation phase.
  - **Procedural**: simple sin/cos on leg/arm proxies (no skeleton); phase from time + follower_id.
- **Phase**: `phase = (time * walkSpeed + follower_id) % 1` so agents are visually de-synced.
- **Lightweight**: No IK, no unique clips; single cycle, instance phase only.

---

## 8. File and Module Overview

| Layer | Files / modules |
|-------|------------------|
| **Schema** | `backend: src/avatar/schema.py` (Pydantic), `frontend: src/types/avatar.ts` |
| **Generation** | `backend: src/avatar/generator.py` (seed → params), used in seeder |
| **DB** | `followers.avatar_seed`, `followers.avatar_params` (migration: `add_follower_avatar_fields.py`) |
| **API** | `FollowerResponse` includes `avatar_seed`, `avatar_params`; custom avatar via POST follower with `avatar_params` |
| **Resolve** | `frontend: src/avatar/resolveAvatar.ts` — same PRNG as backend; `resolveAvatar(seed, params)` → `AvatarParams` |
| **Rendering** | `MapFollower.avatar` is resolved in `toMapFollower()`; future: `world/avatar-*` (instancing / custom layer) |
| **Creator** | `frontend: src/avatar/AvatarCreator.ts` — constants, default params, `avatarParamsToApi()` |
| **Persistence** | Store seed or params only; no model files. |

This design keeps avatars **stylized and lightweight**, supports **multicultural representation** via continuous distributions and varied parts, allows **user-created avatars** with the same schema, and targets **10k+ characters** via shared assets and GPU instancing.
