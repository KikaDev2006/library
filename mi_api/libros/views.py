from typing import Optional

from ninja import File, Form, Router, UploadedFile
from ninja.pagination import paginate

from usuarios.auth import JWTAuth
from .schemas import (
    CapituloIn,
    CapituloListOut,
    CapituloOut,
    CapituloUpdate,
    CategoriaOut,
    ComentarioIn,
    ComentarioOut,
    LibroIn,
    LibroListOut,
    LibroOut,
    LibroUpdate,
    ResenaIn,
    ResenaOut,
)
from .services import (
    actualizar_capitulo,
    actualizar_libro,
    comentar_libro,
    crear_capitulo,
    crear_libro,
    eliminar_capitulo,
    eliminar_comentario,
    eliminar_libro,
    listar_capitulos,
    listar_categorias,
    listar_comentarios,
    listar_libros,
    listar_mis_libros,
    listar_resenas,
    obtener_capitulo,
    obtener_libro,
    puntuar_libro,
)
from .validators import validar_archivo_libro, validar_portada

router = Router()
auth = JWTAuth()


# ── Categorías (solo lectura — se gestionan desde /admin/) ─

@router.get("/categorias", tags=["Listar Categorías"], response=list[CategoriaOut])
def get_categorias(request):
    return listar_categorias()


# ── Libros ──────────────────────────────────────

@router.get("/libros", tags=["Listar Libros Públicos"], response=list[LibroListOut])
@paginate
def get_libros(request, categoria: Optional[int] = None, buscar: Optional[str] = None):
    return listar_libros(categoria=categoria, buscar=buscar)


@router.get("/libros/mios", tags=["Listar Mis Libros"], response=list[LibroListOut], auth=auth)
@paginate
def get_mis_libros(request):
    return listar_mis_libros(request.auth)


@router.get("/libros/{libro_id}", tags=["Obtener Libro por ID"], response=LibroOut)
def get_libro(request, libro_id: int):
    return obtener_libro(libro_id)


@router.post("/libros", tags=["Crear Libro"], response=LibroOut, auth=auth)
def post_libro(
    request,
    data: LibroIn = Form(...),
    portada: UploadedFile = File(None),
    archivo: UploadedFile = File(None),
):
    validar_portada(portada)
    validar_archivo_libro(archivo)
    return crear_libro(request.auth, data, portada, archivo)


@router.put("/libros/{libro_id}", tags=["Actualizar Libro"], response=LibroOut, auth=auth)
def put_libro(
    request,
    libro_id: int,
    data: LibroUpdate = Form(...),
    portada: UploadedFile = File(None),
):
    validar_portada(portada)
    return actualizar_libro(libro_id, request.auth, data, portada)


@router.delete("/libros/{libro_id}", tags=["Eliminar Libro"], auth=auth)
def delete_libro(request, libro_id: int):
    return eliminar_libro(libro_id, request.auth)


# ── Capítulos ─────────────────────────────────

@router.get(
    "/libros/{libro_id}/capitulos", tags=["Listar Capítulos de un Libro"], response=list[CapituloListOut]
)
def get_capitulos(request, libro_id: int):
    return listar_capitulos(libro_id)


@router.get(
    "/libros/{libro_id}/capitulos/{numero}", tags=["Leer Capítulo"], response=CapituloOut
)
def get_capitulo(request, libro_id: int, numero: int):
    return obtener_capitulo(libro_id, numero)


@router.post(
    "/libros/{libro_id}/capitulos", tags=["Crear Capítulo"], response=CapituloOut, auth=auth
)
def post_capitulo(request, libro_id: int, data: CapituloIn):
    return crear_capitulo(libro_id, request.auth, data)


@router.put("/capitulos/{capitulo_id}", tags=["Actualizar Capítulo"], response=CapituloOut, auth=auth)
def put_capitulo(request, capitulo_id: int, data: CapituloUpdate):
    return actualizar_capitulo(capitulo_id, request.auth, data)


@router.delete("/capitulos/{capitulo_id}", tags=["Eliminar Capítulo"], auth=auth)
def delete_capitulo(request, capitulo_id: int):
    return eliminar_capitulo(capitulo_id, request.auth)


# ── Reseñas ─────────────────────────────────────

@router.post("/libros/{libro_id}/resena", tags=["Puntuar Libro"], response=ResenaOut, auth=auth)
def post_resena(request, libro_id: int, data: ResenaIn):
    return puntuar_libro(libro_id, request.auth, data)


@router.get("/libros/{libro_id}/resenas", tags=["Listar Puntuaciones de un Libro"], response=list[ResenaOut])
def get_resenas(request, libro_id: int):
    return listar_resenas(libro_id)


# ── Comentarios ─────────────────────────────────

@router.post(
    "/libros/{libro_id}/comentarios", tags=["Comentar Libro"], response=ComentarioOut, auth=auth
)
def post_comentario(request, libro_id: int, data: ComentarioIn):
    return comentar_libro(libro_id, request.auth, data)


@router.get(
    "/libros/{libro_id}/comentarios", tags=["Listar Comentarios de un Libro"], response=list[ComentarioOut]
)
def get_comentarios(request, libro_id: int):
    return listar_comentarios(libro_id)


@router.delete("/comentarios/{comentario_id}", tags=["Eliminar Comentario"], auth=auth)
def delete_comentario(request, comentario_id: int):
    return eliminar_comentario(comentario_id, request.auth)