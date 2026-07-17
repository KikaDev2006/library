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


# ✅ MODIFICADO: Añadir campos mi_puntuacion y es_favorito
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
    # ✅ NUEVOS CAMPOS
    mi_puntuacion: int | None = None
    mi_resena_id: int | None = None
    es_favorito: bool = False

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


# ✅ MODIFICADO: Añadir campo es_favorito
class LibroListOut(Schema):
    id: int
    titulo: str
    portada: str | None = None
    autor: AutorOut
    categorias: list[CategoriaOut]
    fecha_publicacion: datetime.date | None = None
    promedio_puntuacion: float | None = None
    # ✅ NUEVO CAMPO
    es_favorito: bool = False

    @staticmethod
    def resolve_portada(obj):
        return obj.portada.url if obj.portada else None

    @staticmethod
    def resolve_categorias(obj):
        return list(obj.categorias.all())

    @staticmethod
    def resolve_promedio_puntuacion(obj):
        return getattr(obj, "promedio_puntuacion", None)


# ✅ NUEVO: PagedLibroListOut (si no lo tenías)
class PagedLibroListOut(Schema):
    items: list[LibroListOut]
    count: int


# ✅ NUEVO: Favoritos
class FavoritoOut(Schema):
    id: int  # ← ID del libro
    titulo: str
    portada: str | None = None
    autor: AutorOut
    fecha_publicacion: datetime.date | None = None

    @staticmethod
    def resolve_portada(obj):
        return obj.portada.url if obj.portada else None


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


# ✅ NUEVO: Reordenar capítulos
class ReordenCapitulos(Schema):
    capitulos: list[int]  # IDs en el nuevo orden


# ✅ NUEVO: Auto-guardado de capítulos
class AutoGuardarCapitulo(Schema):
    contenido: str


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


# ═══════════════════════════════════════════════
# ✅ NUEVOS SCHEMAS (Agregar al final del archivo)
# ═══════════════════════════════════════════════

# ── Progreso de Lectura ──────────────────────

class ProgresoOut(Schema):
    libro_id: int
    capitulo_actual_id: int | None = None
    capitulo_numero: int | None = None
    pagina: int = 0
    porcentaje: int = 0
    ultima_lectura: datetime.datetime


class ProgresoIn(Schema):
    capitulo_id: int | None = None
    pagina: int | None = 0
    porcentaje: int | None = 0

    @field_validator("porcentaje")
    @classmethod
    def validar_porcentaje(cls, v):
        if v is not None and (v < 0 or v > 100):
            raise ValueError("El porcentaje debe estar entre 0 y 100")
        return v


# ── Versiones de Capítulos ────────────────────

class VersionCapituloOut(Schema):
    id: int
    contenido: str
    fecha_version: datetime.datetime
    notas: str | None = None
    usuario: AutorOut | None = None


# ── Límite de Ediciones ──────────────────────

# Este schema es solo para respuesta, no para input
class LimiteEdicionOut(Schema):
    fecha: datetime.date
    contador: int
    limite_diario: int = 100
    restantes: int  # Calculado: limite_diario - contador


# ── Usuario (si necesitas extender para vistas) ──

# ✅ NUEVO: Para el perfil del usuario con estadísticas
class UsuarioEstadisticasOut(Schema):
    total_libros: int
    total_resenas: int
    total_comentarios: int
    total_favoritos: int
    libros_publicados: int
    libros_privados: int


# ── Estadísticas de Libro ────────────────────

class LibroEstadisticasOut(Schema):
    libro_id: int
    total_resenas: int
    promedio_puntuacion: float | None = None
    total_comentarios: int
    total_capitulos: int
    total_lectores: int  # Personas que tienen este libro en progreso
    
    
    
 # Notificacion signals


class NotificacionOut(Schema):
    """Schema para las notificaciones que recibe el usuario"""
    id: int
    tipo: str
    mensaje: str
    libro_id: int
    titulo_libro: str
    autor_nombre: str
    autor_id: int
    leida: bool
    fecha_creacion: datetime.datetime