"""
SQLAlchemy 2.0 declarative models for Agentropolis.

All session-scoped tables carry a composite primary key (session_id, <entity>_id)
and a foreign key to sessions with ON DELETE CASCADE.
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# sessions
# ---------------------------------------------------------------------------

class Session(Base):
    __tablename__ = "sessions"

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    virtual_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="paused", server_default="paused"
    )
    config: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=dict)

    # relationships (back-populated for cascade awareness)
    archetypes: Mapped[list["Archetype"]] = relationship(
        back_populates="session", cascade="all, delete-orphan", lazy="noload"
    )
    followers: Mapped[list["Follower"]] = relationship(
        back_populates="session", cascade="all, delete-orphan", lazy="noload"
    )
    companies: Mapped[list["Company"]] = relationship(
        back_populates="session", cascade="all, delete-orphan", lazy="noload"
    )
    memories: Mapped[list["Memory"]] = relationship(
        back_populates="session", cascade="all, delete-orphan", lazy="noload"
    )
    posts: Mapped[list["Post"]] = relationship(
        back_populates="session", cascade="all, delete-orphan", lazy="noload"
    )
    events: Mapped[list["Event"]] = relationship(
        back_populates="session", cascade="all, delete-orphan", lazy="noload"
    )
    relationships_: Mapped[list["Relationship"]] = relationship(
        back_populates="session", cascade="all, delete-orphan", lazy="noload"
    )


# ---------------------------------------------------------------------------
# archetypes
# ---------------------------------------------------------------------------

class Archetype(Base):
    __tablename__ = "archetypes"
    __table_args__ = (
        ForeignKeyConstraint(
            ["session_id"],
            ["sessions.session_id"],
            ondelete="CASCADE",
        ),
    )

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True
    )
    archetype_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    industry: Mapped[str] = mapped_column(String(128), nullable=False)
    social_class: Mapped[str | None] = mapped_column(String(64), nullable=True)
    region: Mapped[str] = mapped_column(String(128), nullable=False)
    home_neighborhood: Mapped[str | None] = mapped_column(String(128), nullable=True)
    work_district: Mapped[str | None] = mapped_column(String(128), nullable=True)

    session: Mapped["Session"] = relationship(back_populates="archetypes", lazy="noload")
    followers: Mapped[list["Follower"]] = relationship(
        back_populates="archetype",
        primaryjoin=(
            "and_(Follower.session_id == Archetype.session_id, "
            "Follower.archetype_id == Archetype.archetype_id)"
        ),
        lazy="noload",
        overlaps="session,followers",
    )


# ---------------------------------------------------------------------------
# followers
# ---------------------------------------------------------------------------

class Follower(Base):
    __tablename__ = "followers"
    __table_args__ = (
        ForeignKeyConstraint(
            ["session_id"],
            ["sessions.session_id"],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["session_id", "archetype_id"],
            ["archetypes.session_id", "archetypes.archetype_id"],
            ondelete="CASCADE",
        ),
        Index("idx_followers_archetype", "session_id", "archetype_id"),
    )

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True
    )
    follower_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    archetype_id: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    gender: Mapped[str | None] = mapped_column(String(32), nullable=True)
    race: Mapped[str | None] = mapped_column(String(64), nullable=True)
    home_position: Mapped[dict] = mapped_column(JSONB, nullable=False)
    work_position: Mapped[dict] = mapped_column(JSONB, nullable=False)
    position: Mapped[dict] = mapped_column(JSONB, nullable=False)
    status_ailments: Mapped[list | None] = mapped_column(
        JSONB, nullable=False, default=list, server_default="[]"
    )
    happiness: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.5, server_default="0.5"
    )
    volatility: Mapped[float] = mapped_column(Float, nullable=False)
    avatar_seed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    avatar_params: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    home_neighborhood: Mapped[str | None] = mapped_column(String(128), nullable=True)
    work_district: Mapped[str | None] = mapped_column(String(128), nullable=True)

    session: Mapped["Session"] = relationship(
        back_populates="followers", lazy="noload", overlaps="followers"
    )
    archetype: Mapped["Archetype"] = relationship(
        back_populates="followers",
        primaryjoin=(
            "and_(Follower.session_id == Archetype.session_id, "
            "Follower.archetype_id == Archetype.archetype_id)"
        ),
        foreign_keys="[Follower.session_id, Follower.archetype_id]",
        lazy="noload",
        overlaps="followers,session",
    )


# ---------------------------------------------------------------------------
# companies
# ---------------------------------------------------------------------------

class Company(Base):
    __tablename__ = "companies"
    __table_args__ = (
        ForeignKeyConstraint(
            ["session_id"],
            ["sessions.session_id"],
            ondelete="CASCADE",
        ),
    )

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True
    )
    company_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    industry: Mapped[str] = mapped_column(String(128), nullable=False)
    region: Mapped[str] = mapped_column(String(128), nullable=False)
    position: Mapped[dict] = mapped_column(JSONB, nullable=False)
    work_district: Mapped[str | None] = mapped_column(String(128), nullable=True)

    session: Mapped["Session"] = relationship(back_populates="companies", lazy="noload")


# ---------------------------------------------------------------------------
# memories
# ---------------------------------------------------------------------------

class Memory(Base):
    __tablename__ = "memories"
    __table_args__ = (
        ForeignKeyConstraint(
            ["session_id"],
            ["sessions.session_id"],
            ondelete="CASCADE",
        ),
        Index("idx_memories_agent_time", "session_id", "archetype_id", "virtual_time"),
    )

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True
    )
    memory_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    archetype_id: Mapped[int] = mapped_column(Integer, nullable=False)
    virtual_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    action_type: Mapped[str] = mapped_column(String(64), nullable=False)
    action_params: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=dict)
    duration: Mapped[float] = mapped_column(Float, nullable=False)
    thinking: Mapped[str] = mapped_column(Text, nullable=False)

    session: Mapped["Session"] = relationship(back_populates="memories", lazy="noload")


# ---------------------------------------------------------------------------
# posts
# ---------------------------------------------------------------------------

class Post(Base):
    __tablename__ = "posts"
    __table_args__ = (
        ForeignKeyConstraint(
            ["session_id"],
            ["sessions.session_id"],
            ondelete="CASCADE",
        ),
        Index("idx_posts_session_time", "session_id", "virtual_time"),
    )

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True
    )
    post_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    follower_id: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    virtual_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    session: Mapped["Session"] = relationship(back_populates="posts", lazy="noload")


# ---------------------------------------------------------------------------
# events
# ---------------------------------------------------------------------------

class Event(Base):
    __tablename__ = "events"
    __table_args__ = (
        ForeignKeyConstraint(
            ["session_id"],
            ["sessions.session_id"],
            ondelete="CASCADE",
        ),
        Index("idx_events_session_time", "session_id", "virtual_time"),
    )

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True
    )
    event_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    virtual_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    session: Mapped["Session"] = relationship(back_populates="events", lazy="noload")


# ---------------------------------------------------------------------------
# relationships
# ---------------------------------------------------------------------------

_VALID_RELATION_TYPES = ("employee", "employer", "married", "friends", "enemies", "family", "coworker")


class Relationship(Base):
    __tablename__ = "relationships"
    __table_args__ = (
        ForeignKeyConstraint(
            ["session_id"],
            ["sessions.session_id"],
            ondelete="CASCADE",
        ),
        CheckConstraint(
            "relation_type IN ('employee', 'employer', 'married', 'friends', 'enemies', 'family', 'coworker')",
            name="ck_relationships_relation_type",
        ),
        Index("idx_relationships_f1", "session_id", "follower1_id"),
        Index("idx_relationships_f2", "session_id", "follower2_id"),
    )

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True
    )
    relation_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    follower1_id: Mapped[int] = mapped_column(Integer, nullable=False)
    follower2_id: Mapped[int] = mapped_column(Integer, nullable=False)
    relation_strength: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.5, server_default="0.5"
    )
    relation_type: Mapped[str] = mapped_column(String(32), nullable=False)

    session: Mapped["Session"] = relationship(back_populates="relationships_", lazy="noload")


# ---------------------------------------------------------------------------
# locations  (NOT session-scoped — shared reference data)
# ---------------------------------------------------------------------------

class Location(Base):
    __tablename__ = "locations"
    __table_args__ = (
        Index("idx_locations_region", "region"),
    )

    location_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    type: Mapped[str] = mapped_column(String(64), nullable=False)
    region: Mapped[str] = mapped_column(String(128), nullable=False)
    position: Mapped[dict] = mapped_column(JSONB, nullable=False)
    # "metadata" is a reserved attribute name on DeclarativeBase; use metadata_
    metadata_: Mapped[dict | None] = mapped_column(
        "metadata", JSONB, nullable=True
    )


# ---------------------------------------------------------------------------
# demographics
# ---------------------------------------------------------------------------

class Demographic(Base):
    __tablename__ = "demographics"
    __table_args__ = (
        ForeignKeyConstraint(
            ["session_id"],
            ["sessions.session_id"],
            ondelete="CASCADE",
        ),
    )

    demographic_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    session_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    is_company: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    industry: Mapped[str | None] = mapped_column(String(128), nullable=True)
    social_class: Mapped[str | None] = mapped_column(String(64), nullable=True)
    region: Mapped[str | None] = mapped_column(String(128), nullable=True)
    home_neighborhood: Mapped[str | None] = mapped_column(String(128), nullable=True)
    work_district: Mapped[str | None] = mapped_column(String(128), nullable=True)
