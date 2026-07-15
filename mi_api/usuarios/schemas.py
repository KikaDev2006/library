import datetime

from ninja import Schema
from pydantic import Field, field_validator


class UsuarioIn(Schema):
    username: str
    password: str = Field(..., min_length=8)
    password_confirm: str
    email: str | None = None

    @field_validator("password_confirm")
    @classmethod
    def passwords_match(cls, v, info):
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("Las contraseñas no coinciden")
        return v


# Datos que devuelves al cliente autenticado (su propio perfil, incluye email)
class UsuarioOut(Schema):
    id: int
    username: str
    email: str | None = None
    fecha_registro: datetime.datetime | None = None


# Datos públicos de un usuario (sin email)
class UsuarioPublicOut(Schema):
    id: int
    username: str
    fecha_registro: datetime.datetime | None = None


class LoginIn(Schema):
    email: str
    password: str


class LoginOut(Schema):
    message: str


class UsuarioUpdate(Schema):
    username: str | None = None
    email: str | None = None
    password: str | None = None


class TokenOut(Schema):
    token: str