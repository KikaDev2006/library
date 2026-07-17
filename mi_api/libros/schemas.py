import datetime
import re

from ninja import Schema
from pydantic import Field, field_validator

URL_PATTERN = re.compile(r"((https?|ftp)://|www\.)\S+", re.IGNORECASE)


def _validar_sin_links(texto: str) -> str:
    if texto and URL_PATTERN.search(texto):
        raise ValueError("No está permitido incluir enlaces en el contenido")
    return texto


# ── Categoría ──────────────────────────────────

class CategoriaOut(Schema):
    id: int
    nombre: str
    descripcion: str | None = None





# ── Libro ──────────────────────────────────────

class LibroIn(Schema):
    titulo: str = Field(..., min_length=1, max_length=255)
    tipo: str
    descripcion: str | None = None
    categorias: list[int] = []
    paginas: int | None = None
    fecha_publicacion: datetime.date | None = None
    visibilidad: str = "privado"

    @field_validator("tipo")
    @classmethod
    def validar_tipo(cls, v):
        if v not in ("escrito", "subido"):
            raise ValueError("tipo debe ser 'escrito' o 'subido'")
        return v

    @field_validator("visibilidad")
    @classmethod
    def validar_visibilidad(cls, v):
        if v not in ("publico", "privado"):
            raise ValueError("visibilidad debe ser 'publico' o 'privado'")
        return v

    @field_validator("descripcion")
    @classmethod
    def sin_links_descripcion(cls, v):
        if v is not None:
            return _validar_sin_links(v)
        return v


class LibroUpdate(Schema):
    titulo: str | None = None
    descripcion: str | None = None
    categorias: list[int] | None = None
    paginas: int | None = None
    fecha_publicacion: datetime.date | None = None
    visibilidad: str | None = None

    @field_validator("descripcion")
    @classmethod
    def sin_links_descripcion(cls, v):
        if v is not None:
            return _validar_sin_links(v)
        return v


class AutorOut(Schema):
    id: int
    username: str


class LibroOut(Schema):
    id: int
    titulo: str
    portada: str | None = None
    autor: AutorOut
    tipo: str
    archivo: str | None = None
    descripcion: str | None = None
    categorias: list[CategoriaOut]
    paginas: int | None = None
    fecha_publicacion: datetime.date | None = None
    fecha_creacion: datetime.datetime
    visibilidad: str
    promedio_puntuacion: float | None = None

    @staticmethod
    def resolve_portada(obj):
        return obj.portada.url if obj.portada else None

    @staticmethod
    def resolve_archivo(obj):
        return obj.archivo.url if obj.archivo else None

    @staticmethod
    def resolve_categorias(obj):
        return list(obj.categorias.all())

    @staticmethod
    def resolve_promedio_puntuacion(obj):
        return getattr(obj, "promedio_puntuacion", None)


class LibroListOut(Schema):
    id: int
    titulo: str
    portada: str | None = None
    autor: AutorOut
    categorias: list[CategoriaOut]
    fecha_publicacion: datetime.date | None = None
    promedio_puntuacion: float | None = None

    @staticmethod
    def resolve_portada(obj):
        return obj.portada.url if obj.portada else None

    @staticmethod
    def resolve_categorias(obj):
        return list(obj.categorias.all())

    @staticmethod
    def resolve_promedio_puntuacion(obj):
        return getattr(obj, "promedio_puntuacion", None)


# ── Capítulo ────────────────────────────────────

class CapituloIn(Schema):
    numero: int = Field(..., ge=1)
    titulo: str = Field(..., min_length=1, max_length=255)
    contenido: str

    @field_validator("contenido")
    @classmethod
    def sin_links(cls, v):
        return _validar_sin_links(v)


class CapituloUpdate(Schema):
    numero: int | None = None
    titulo: str | None = None
    contenido: str | None = None

    @field_validator("contenido")
    @classmethod
    def sin_links(cls, v):
        if v is not None:
            return _validar_sin_links(v)
        return v


class CapituloOut(Schema):
    id: int
    libro_id: int
    numero: int
    titulo: str
    contenido: str
    fecha_creacion: datetime.datetime
    fecha_actualizacion: datetime.datetime


class CapituloListOut(Schema):
    id: int
    numero: int
    titulo: str


# ── Reseña ──────────────────────────────────────

class ResenaIn(Schema):
    puntuacion: int = Field(..., ge=1, le=5)


class ResenaOut(Schema):
    id: int
    libro_id: int
    usuario: AutorOut
    puntuacion: int
    fecha_creacion: datetime.datetime


# ── Comentario ──────────────────────────────────

class ComentarioIn(Schema):
    texto: str = Field(..., min_length=1)

    @field_validator("texto")
    @classmethod
    def sin_links(cls, v):
        return _validar_sin_links(v)


class ComentarioOut(Schema):
    id: int
    libro_id: int
    usuario: AutorOut
    texto: str
    fecha_creacion: datetime.datetime