import uuid
from datetime import datetime, timezone
from sqlmodel import Field,Column
from pydantic import computed_field
from sqlalchemy.dialects import postgresql as pg
from sqlalchemy import text, func
from backend.app.auth.schema import BaseUserSchema, RoleChoicesSchema

class User(BaseUserSchema, table=True):
    # """
    # User database model representing the physical 'user' table in PostgreSQL.
    # Inherits fields from BaseUserSchema and registers as a SQLModel table.
    # """
    __tablename__ = "user"

    # Primary Key configured with PostgreSQL Native UUID type
    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(
            pg.UUID(as_uuid=True),
            primary_key=True
        )
    )
    
    # Hashed Password string required for auth validation
    hashed_password: str = Field()
    
    # Track failed attempts using PostgreSQL SmallInteger to conserve storage
    failed_login_attempts: int = Field(
        default=0,
        sa_type=pg.SMALLINT
    )
    
    # Timestamp tracking for security lockouts
    last_failed_login: datetime | None = Field(
        default=None,
        sa_column=Column(
            pg.TIMESTAMP(timezone=True),
            nullable=True
        )
    )
    
    # OTP credentials for logins and authentication flow
    otp: str = Field(default="", max_length=6)
    
    otp_expiry_time: datetime | None = Field(
        default=None,
        sa_column=Column(
            pg.TIMESTAMP(timezone=True),
            nullable=True
        )
    )
    
    # Record creation timestamp mapped to DB Server CURRENT_TIMESTAMP
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(
            pg.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=text("current_timestamp")
        )
    )
    
    # Record modification timestamp with automatic updates on row writes
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(
            pg.TIMESTAMP(timezone=True),
            nullable=False,
            onupdate=func.current_timestamp(),
            server_default=text("current_timestamp")
        )
    )

    # ==========================================
    # COMPUTED FIELDS & UTILITIES
    # ==========================================

    @computed_field
    @property
    def full_name(self) -> str:
        # """
        # Dynamically constructs the user's full name.
        # Capitalises characters and strips trailing spaces gracefully.
        # """
        full_name = f"{self.first_name} {self.middle_name + ' ' if self.middle_name else ''}{self.last_name}"
        return full_name.title().strip()

    def has_role(self, role: RoleChoicesSchema) -> bool:
        """
        Helper method to verify if the user matches a specified authorization role.
        """
        return self.user_role.value == role.value
