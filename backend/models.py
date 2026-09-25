from datetime import datetime
from typing import Any, List, Optional
from sqlalchemy import DateTime, Float, ForeignKey, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

try:
    from backend.database import Base
except ImportError:
    from .database import Base


class TelemetryLog(Base):
    """Stores incoming sensor telemetry (NPK, pH, moisture, climate)."""
    __tablename__ = "telemetry_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    machine_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, index=True, server_default=func.now(), nullable=False
    )
    n: Mapped[float] = mapped_column(Float, nullable=False)
    p: Mapped[float] = mapped_column(Float, nullable=False)
    k: Mapped[float] = mapped_column(Float, nullable=False)
    ph: Mapped[float] = mapped_column(Float, nullable=False)
    moisture: Mapped[float] = mapped_column(Float, nullable=False)
    temperature: Mapped[float] = mapped_column(Float, nullable=False)
    humidity: Mapped[float] = mapped_column(Float, nullable=False)
    rainfall: Mapped[float] = mapped_column(Float, nullable=False)

    # Relationships
    recommendations: Mapped[List["CropRecommendation"]] = relationship(
        back_populates="telemetry", cascade="all, delete-orphan"
    )


class CropRecommendation(Base):
    """Stores ML-predicted top crop and secondary crops JSON."""
    __tablename__ = "crop_recommendations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    telemetry_id: Mapped[int] = mapped_column(
        ForeignKey("telemetry_logs.id"), index=True, nullable=False
    )
    top_crop: Mapped[str] = mapped_column(String(64), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    secondary_crops: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    # Relationships
    telemetry: Mapped["TelemetryLog"] = relationship(back_populates="recommendations")
    prescriptions: Mapped[List["Prescription"]] = relationship(
        back_populates="recommendation", cascade="all, delete-orphan"
    )


class Prescription(Base):
    """Stores fertilizer & soil amendment quantities calculated by agronomic engine."""
    __tablename__ = "prescriptions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    recommendation_id: Mapped[int] = mapped_column(
        ForeignKey("crop_recommendations.id"), index=True, nullable=False
    )
    urea_kg: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    dap_kg: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    mop_kg: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    lime_kg: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    gypsum_kg: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    # Relationships
    recommendation: Mapped["CropRecommendation"] = relationship(
        back_populates="prescriptions"
    )
