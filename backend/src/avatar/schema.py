"""
Avatar parameter schema — shared contract for procedural and user-created avatars.

Stored in DB as JSONB (avatar_params). No photos; all appearance is parameter-driven.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


BodyType = Literal["slim", "average", "broad"]
HairTexture = Literal["straight", "wavy", "curly", "coily"]
HairStyle = Literal[
    "short", "long", "fade", "bun", "braids", "afro", "ponytail"
]
OutfitType = Literal[
    "casual", "professional", "student", "athletic", "construction", "service"
]


class AvatarParams(BaseModel):
    """Appearance parameters for one avatar. Deterministic from seed or user-defined."""

    skin_tone: float = Field(ge=0.0, le=1.0, description="0=light, 1=dark")
    body_type: BodyType = "average"
    hair_texture: HairTexture = "straight"
    hair_style: HairStyle = "short"
    hair_color: str = Field(description="Hex color or palette id", max_length=32)
    outfit: OutfitType = "casual"
    outfit_color: str = Field(description="Hex color or palette id", max_length=32)
    accessories: list[str] = Field(
        default_factory=list,
        description="e.g. ['glasses', 'bag']",
        max_length=8,
    )

    model_config = {"extra": "forbid"}


# Aliases for API (snake_case in DB/API, frontend may use camelCase)
CustomAvatar = AvatarParams
