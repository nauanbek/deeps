"""
Template model for agent configuration templates.

Represents pre-configured agent templates that users can use to
quickly create new agents with standardized settings.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from core.database import Base

if TYPE_CHECKING:
    from .user import User


class Template(Base):
    """
    Represents an agent configuration template.

    Templates allow users to quickly create agents from pre-configured
    settings, making it easier to get started and standardizing common
    agent configurations across the platform.

    Template Structure:
    - Basic metadata (name, description, category, tags)
    - Agent configuration template (model settings, prompts, features)
    - Visibility settings (public, featured)
    - Usage tracking (use_count for popularity)

    Relationships:
    - Many-to-one with User (template creator)
    """

    __tablename__ = "templates"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Core identification
    name: Mapped[str] = mapped_column(
        String(200), nullable=False, unique=True, index=True
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # Categorization and discovery
    category: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # research, coding, customer_support, etc.
    tags: Mapped[list[str]] = mapped_column(
        JSON, nullable=False, default=list
    )  # Searchable tags

    # Agent configuration template stored as JSON
    # Contains: model_provider, model_name, system_prompt, temperature,
    # max_tokens, planning_enabled, filesystem_enabled, tool_ids, additional_config
    config_template: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)

    # Visibility and prominence
    is_public: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, index=True
    )
    is_featured: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, index=True
    )

    # Usage tracking for popularity metrics
    use_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, index=True
    )

    # Foreign keys
    created_by_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Audit trail
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        onupdate=func.now(),
        nullable=True,
    )

    # Soft delete support
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False, index=True)

    # Relationships
    created_by_user: Mapped["User"] = relationship(
        "User",
        back_populates="templates",
        foreign_keys=[created_by_id],
    )

    # Composite indexes for common query patterns
    __table_args__ = (
        Index("idx_templates_category_active", "category", "is_active"),
        Index("idx_templates_public_featured", "is_public", "is_featured"),
        Index("idx_templates_use_count_desc", "use_count"),
        Index("idx_templates_created_by_active", "created_by_id", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<Template(id={self.id}, name='{self.name}', category='{self.category}', use_count={self.use_count})>"
