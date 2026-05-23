from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from .database import Base


EmbeddingType = JSONB().with_variant(JSON(), "sqlite")


class MediaType(StrEnum):
    IMAGE = "image"
    VIDEO = "video"


class ProcessingStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class MediaItem(Base):
    __tablename__ = "media_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    file_path: Mapped[str] = mapped_column(String(1024))
    original_filename: Mapped[str] = mapped_column(String(512))
    media_type: Mapped[str] = mapped_column(String(16), index=True)
    mime_type: Mapped[str] = mapped_column(String(255), default="")
    file_size: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(32), default=ProcessingStatus.PENDING, index=True)
    duration: Mapped[float | None] = mapped_column(Float, nullable=True)
    caption: Mapped[str] = mapped_column(Text, default="")
    embedding: Mapped[list[float] | None] = mapped_column(EmbeddingType, nullable=True)
    index_key: Mapped[str] = mapped_column(String(255), default="", index=True)
    error_message: Mapped[str] = mapped_column(Text, default="")
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    enqueued_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    scenes: Mapped[list["VideoScene"]] = relationship(
        back_populates="media",
        cascade="all, delete-orphan",
        order_by="VideoScene.scene_index",
    )

    __table_args__ = (Index("ix_media_items_media_type_status", "media_type", "status"),)

    @property
    def is_image(self) -> bool:
        return self.media_type == MediaType.IMAGE

    @property
    def is_video(self) -> bool:
        return self.media_type == MediaType.VIDEO


class VideoScene(Base):
    __tablename__ = "video_scenes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    media_id: Mapped[int] = mapped_column(ForeignKey("media_items.id", ondelete="CASCADE"), index=True)
    scene_index: Mapped[int] = mapped_column(Integer)
    start_time: Mapped[float] = mapped_column(Float)
    end_time: Mapped[float] = mapped_column(Float)
    keyframe_path: Mapped[str] = mapped_column(String(1024), default="")
    thumbnail_path: Mapped[str] = mapped_column(String(1024), default="")
    caption: Mapped[str] = mapped_column(Text, default="")
    embedding: Mapped[list[float] | None] = mapped_column(EmbeddingType, nullable=True)
    index_key: Mapped[str] = mapped_column(String(255), default="", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    media: Mapped[MediaItem] = relationship(back_populates="scenes")

    __table_args__ = (
        UniqueConstraint("media_id", "scene_index", name="uq_video_scenes_media_scene_index"),
        CheckConstraint("end_time >= start_time", name="ck_video_scenes_end_after_start"),
    )
