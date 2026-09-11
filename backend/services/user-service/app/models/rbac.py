"""RBAC: roles, permissions and the two join tables."""

from datetime import datetime

from common.db import Base, IdMixin, TimestampMixin
from sqlalchemy import BigInteger, Boolean, DateTime, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column


class Role(IdMixin, TimestampMixin, Base):
    __tablename__ = "roles"

    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role_type: Mapped[str] = mapped_column(String(32), nullable=False, default="CUSTOM")
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sort_order: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)


class Permission(IdMixin, TimestampMixin, Base):
    __tablename__ = "permissions"

    code: Mapped[str] = mapped_column(String(128), nullable=False)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    module: Mapped[str] = mapped_column(String(32), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)


class RolePermission(IdMixin, TimestampMixin, Base):
    __tablename__ = "role_permissions"

    role_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    permission_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    granted_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)


class UserRole(IdMixin, TimestampMixin, Base):
    __tablename__ = "user_roles"

    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    role_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    granted_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    granted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)