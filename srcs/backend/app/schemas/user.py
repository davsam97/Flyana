"""User schemas"""

from __future__ import annotations

import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator
from typing import Literal

from app.models.enums import Role

DISPLAY_NAME_RE = re.compile(r"^[a-zA-Z0-9_-]{3,24}$")

COMMON_PASSWORDS = frozenset({
    "password12", "password123", "1234567890", "qwertyuiop", "azertyuiop",
    "motdepasse", "administrator", "abc12345678"
})


class UserCreate(BaseModel):
    """What a signup request must contain"""

    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
    display_name: str
    accept_terms: bool

    @field_validator("display_name")
    @classmethod
    def _display_name_shape(cls, v: str) -> str:
        """Keeps display names to safe printable characters"""
        if not DISPLAY_NAME_RE.match(v):
            raise ValueError("Length must be 3 to 24, only characters in [a-z, A-Z, 0-9, _ or -]")
        return v

    @field_validator("password")
    @classmethod
    def _password_not_common(cls, v: str) -> str:
        """Rejects the handful of passwords everyone tries first"""
        if v.lower() in COMMON_PASSWORDS:
            raise ValueError("Password too weak")
        return v

    @field_validator("password")
    @classmethod
    def _password_mixes_classes(cls, v: str) -> str:
        """Needs a lowercase, an uppercase, a digit and a special character"""
        if not any(c.islower() for c in v):
            raise ValueError("Password needs a lowercase letter")
        if not any(c.isupper() for c in v):
            raise ValueError("Password needs an uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password needs a digit")
        if all(c.isalnum() for c in v):
            raise ValueError("Password needs a special character")
        return v

    @field_validator("accept_terms")
    @classmethod
    def _terms_accepted(cls, v: bool) -> bool:
        """No account without an explicit yes to the terms of service"""
        if not v:
            raise ValueError("Terms of service must be accepted")
        return v

    @model_validator(mode="after")
    def _password_differs_from_email(self) -> "UserCreate":
        """Stops the password being the email itself"""
        if self.password.lower() == self.email.lower():
            raise ValueError("Password cannot be the email")
        return self


class UserLogin(BaseModel):
    """What a login request must contain"""

    email: EmailStr
    password: str


class UserPublic(BaseModel):
    """The only shape user data is ever sent out in"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    display_name: str
    avatar_path: str | None
    bio: str | None
    locale: str
    role: Role
    totp_enabled: bool
    created_at: datetime
    xp: int
    level: int
    xp_max: int
    level_xp: int
    streak: int
    has_password: bool

class AccountDeleteRequest(BaseModel):
    """Proof the owner really wants the account gone

    `confirmation` is the display name typed back. `password` is required for
    a password account, an OAuth-only account has none to give.
    """

    confirmation: str = Field(max_length=64)
    password: str | None = Field(default=None, max_length=128)

class UserSummary(BaseModel):
    """A user reduced to what is safe to show anyone

    No email, no role, no 2FA state: this is the shape that rides inside a
    friends list, a conversation header or a search result. `UserPublic` stays
    reserved for `/auth/me`, where the caller is looking at their own account.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    display_name: str
    avatar_path: str | None


# Where the viewer stands relative to the profile they are looking at. Built by
# the route, never stored: "pending_in" means "they asked me", "pending_out"
# means "I asked them".
FriendshipView = Literal[
    "none", "pending_in", "pending_out", "friends", "blocked"
]


class ProfileOut(UserSummary):
    """A public profile: `UserSummary` plus the fields worth reading about
    someone, plus the computed flags the UI needs to draw its buttons
    """

    bio: str | None
    role: Role
    created_at: datetime
    online: bool
    friendship: FriendshipView
    # id of the friendship row, when there is one — lets the profile page
    # accept / decline / remove without loading the whole friends list
    friendship_id: int | None = None


class UserUpdate(BaseModel):
    """The fields a user may change on their own profile

    Acts as a whitelist so a client sending `{"role": "admin"}` cannot promote itself
    """

    display_name: str | None = None
    bio: str | None = Field(default=None, max_length=500)
    locale: Literal["en", "fr"] | None = None

    @field_validator("display_name")
    @classmethod
    def _shape(cls, v: str | None) -> str | None:
        """Same display name rule as on signup applied to edits"""
        if v is not None and not DISPLAY_NAME_RE.match(v):
            raise ValueError("Length must be 3 to 24, only characters in [a-z, A-Z, 0-9, _ or -]")
        return v
