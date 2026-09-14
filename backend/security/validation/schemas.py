"""WebSecKit — Pydantic schemas."""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class PaginationQuery(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class LoginBody(BaseModel):
    model_config = {"extra": "forbid"}
    email: EmailStr
    password: str = Field(min_length=1, max_length=256)


class ContactBody(BaseModel):
    model_config = {"extra": "forbid"}
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    message: str = Field(min_length=1, max_length=5000)
    website: str | None = Field(default="", max_length=0)
