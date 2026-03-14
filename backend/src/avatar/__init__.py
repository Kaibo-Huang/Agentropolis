"""
Procedural avatar system for Agentropolis.

- AvatarParams: schema for avatar appearance (shared with frontend).
- generate_avatar_from_seed: deterministic seed → AvatarParams for diversity.
- resolve_avatar: follower.avatar_params or generate_avatar_from_seed(follower.avatar_seed).
"""

from src.avatar.schema import AvatarParams
from src.avatar.generator import generate_avatar_from_seed, resolve_avatar

__all__ = [
    "AvatarParams",
    "generate_avatar_from_seed",
    "resolve_avatar",
]
