"""
Deterministic avatar generation from a seed.

Uses a simple PRNG (mulberry32) so the same seed always produces the same
avatar. Diversity via continuous distributions (skin tone) and weighted
discrete choices (hair, outfit). No hard-coded races; multicultural mix
through parameter distributions.
"""

from __future__ import annotations

from typing import Any, TypeVar

from src.avatar.schema import (
    AvatarParams,
    BodyType,
    HairStyle,
    HairTexture,
    OutfitType,
)

# ---------------------------------------------------------------------------
# PRNG: mulberry32 (deterministic, one uint32 state)
# ---------------------------------------------------------------------------


def _mulberry32_next(seed: int) -> int:
    """Return next state from mulberry32. Seed is mutable in caller."""
    seed = (seed + 0x6D2B79F5) & 0xFFFFFFFF  # 32-bit
    return seed


def _random(seed: int) -> tuple[float, int]:
    """Uniform [0, 1), returns (value, next_seed)."""
    next_seed = _mulberry32_next(seed)
    return (next_seed / 0xFFFFFFFF, next_seed)


def _randint(seed: int, lo: int, hi: int) -> tuple[int, int]:
    """Inclusive [lo, hi], returns (value, next_seed)."""
    u, next_seed = _random(seed)
    return (lo + int(u * (hi - lo + 1)) % (hi - lo + 1), next_seed)


T = TypeVar("T")


def _choice(seed: int, items: list[T], weights: list[float] | None = None) -> tuple[T, int]:
    """Pick one item; optional weights. Returns (item, next_seed)."""
    if weights is None:
        i, next_seed = _randint(seed, 0, len(items) - 1)
        return (items[i], next_seed)
    total = sum(weights)
    u, next_seed = _random(seed)
    r = u * total
    for i, w in enumerate(weights):
        r -= w
        if r <= 0:
            return (items[i], next_seed)
    return (items[-1], next_seed)


# ---------------------------------------------------------------------------
# Palettes and options (stylized, no photos)
# ---------------------------------------------------------------------------

SKIN_PALETTE = [
    "#f5e6d3", "#e8d5c4", "#d4b896", "#c4a574", "#a67c52",
    "#8d5524", "#6b4423", "#5c3d22", "#4a3728", "#2d1f14",
]
# Continuous skin_tone [0,1] maps to index; we interpolate or pick nearest

HAIR_COLORS = [
    "#1a1a1a", "#2d2d2d", "#4a3728", "#5c4033", "#6b4423",
    "#8d5524", "#a67c52", "#c4a574", "#d4b896", "#e8d5c4",
    "#deb887", "#daa520", "#b8860b", "#8b4513", "#654321",
    "#2d1f14", "#1a1a1a", "#4a4a4a", "#6b6b6b", "#8b7355",
]

OUTFIT_COLORS = [
    "#2c3e50", "#34495e", "#7f8c8d", "#95a5a6", "#bdc3c7",
    "#e74c3c", "#c0392b", "#e67e22", "#d35400", "#f39c12",
    "#27ae60", "#16a085", "#2980b9", "#3498db", "#9b59b6",
    "#8e44ad", "#2c3e50", "#1abc9c", "#f1c40f", "#ecf0f1",
]

BODY_TYPES: list[BodyType] = ["slim", "average", "broad"]
BODY_WEIGHTS = [0.25, 0.50, 0.25]

HAIR_TEXTURES: list[HairTexture] = ["straight", "wavy", "curly", "coily"]
HAIR_TEXTURE_WEIGHTS = [0.35, 0.30, 0.22, 0.13]

HAIR_STYLES: list[HairStyle] = [
    "short", "long", "fade", "bun", "braids", "afro", "ponytail"
]
# Slightly weighted toward short/long for variety
HAIR_STYLE_WEIGHTS = [0.22, 0.20, 0.12, 0.14, 0.12, 0.10, 0.10]

OUTFIT_TYPES: list[OutfitType] = [
    "casual", "professional", "student", "athletic", "construction", "service"
]
OUTFIT_WEIGHTS_DEFAULT = [0.30, 0.20, 0.15, 0.15, 0.10, 0.10]

# Industry bias: professional/construction/service by industry
INDUSTRY_OUTFIT_BIAS: dict[str, list[float]] = {
    "Finance": [0.10, 0.55, 0.05, 0.10, 0.05, 0.15],
    "Tech": [0.35, 0.25, 0.15, 0.15, 0.05, 0.05],
    "Healthcare": [0.15, 0.25, 0.10, 0.10, 0.05, 0.35],
    "Retail": [0.25, 0.10, 0.15, 0.10, 0.05, 0.35],
    "Manufacturing": [0.15, 0.10, 0.05, 0.15, 0.45, 0.10],
    "Government": [0.15, 0.50, 0.10, 0.10, 0.05, 0.10],
    "Education": [0.20, 0.25, 0.35, 0.10, 0.05, 0.05],
}

ACCESSORY_OPTIONS = ["glasses", "hat", "bag", "scarf"]
ACCESSORY_PROBABILITY = 0.35  # per slot, approximate

# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------


def generate_avatar_from_seed(
    seed: int,
    *,
    industry: str | None = None,
    social_class: str | None = None,
) -> AvatarParams:
    """
    Deterministic avatar parameters from a single integer seed.

    Optional industry/social_class bias outfit choice (e.g. Finance → more
    professional). Same seed always yields same params.
    """
    s = seed & 0xFFFFFFFF
    if s == 0:
        s = 1

    # Skin tone: continuous [0, 1] from two randoms for finer resolution
    u1, s = _random(s)
    u2, s = _random(s)
    t = (u1 + u2) / 2.0
    t = max(0.0, min(1.0, t))
    idx = int(t * (len(SKIN_PALETTE) - 1) + 0.5)
    skin_hex = SKIN_PALETTE[max(0, min(idx, len(SKIN_PALETTE) - 1))]

    body_type, s = _choice(s, BODY_TYPES, BODY_WEIGHTS)
    hair_texture, s = _choice(s, HAIR_TEXTURES, HAIR_TEXTURE_WEIGHTS)
    hair_style, s = _choice(s, HAIR_STYLES, HAIR_STYLE_WEIGHTS)
    hair_color, s = _choice(s, HAIR_COLORS, None)

    outfit_weights = (
        INDUSTRY_OUTFIT_BIAS.get(industry or "", OUTFIT_WEIGHTS_DEFAULT)
        if industry
        else OUTFIT_WEIGHTS_DEFAULT
    )
    outfit, s = _choice(s, OUTFIT_TYPES, outfit_weights)
    outfit_color, s = _choice(s, OUTFIT_COLORS, None)

    accessories: list[str] = []
    for opt in ACCESSORY_OPTIONS:
        u, s = _random(s)
        if u < ACCESSORY_PROBABILITY:
            accessories.append(opt)

    return AvatarParams(
        skin_tone=t,
        body_type=body_type,
        hair_texture=hair_texture,
        hair_style=hair_style,
        hair_color=hair_color,
        outfit=outfit,
        outfit_color=outfit_color,
        accessories=accessories,
    )


def resolve_avatar(
    *,
    avatar_seed: int | None = None,
    avatar_params: dict[str, Any] | None = None,
) -> AvatarParams | None:
    """
    Resolve final AvatarParams from stored follower data.

    - If avatar_params is set (e.g. custom avatar), validate and return.
    - Else if avatar_seed is set, generate from seed and return.
    - Else return None (caller can fall back to default or circle).
    """
    if avatar_params is not None:
        return AvatarParams.model_validate(avatar_params)
    if avatar_seed is not None:
        return generate_avatar_from_seed(avatar_seed)
    return None
