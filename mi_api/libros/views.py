from typing import Optional

from ninja import File, Form, Router, UploadedFile
from ninja.pagination import paginate
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.core.exceptions import PermissionDenied
from datetime import date

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
    # ✅ NUEVOS IMPORTS
    FavoritoOut,
    ProgresoOut,
    ProgresoIn,
    VersionCapituloOut,
    ReordenCapitulos,
    AutoGuardarCapitulo,
    PagedLibroListOut,
    NotificacionOut,
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
    obtener_estadisticas_libro,
    obtener_libro,
    puntuar_libro,
    reordenar_capitulos,
    listar_favoritos,
    obtener_notificaciones,
    contar_notificaciones_no_leidas,
    marcar_notificaciones_leidas,
    marcar_notificacion_leida,
    eliminar_notificacion,
    eliminar_todas_notificaciones,
)  # ✅ Alias para evitar conflicto

from .validators import validar_archivo_libro, validar_portada
from .models import ProgresoLectura, VersionCapitulo, LimiteEdicionDiario ,Notificacion # ✅ NUEVO

# ✅ NUEVO: Función de sanitización
from .utiles import sanitizar_contenido_tiptap  # Crearemos este archivo

router = Router()
auth = JWTAuth()


# ── Categorías (solo lectura — se gestionan desde /admin/) ─

@router.get("/categorias", tags=["Listar Categorías"], response=list[CategoriaOut])
def get_categorias(request):
    return listar_categorias()


# ── Libros ──────────────────────────────────────

# views.py - Corregir el endpoint get_libros
# views.py - Asegurar que get_libros pase user correctamente

@router.get("/libros", tags=["Listar Libros Públicos"], response=list[LibroListOut])
@paginate
def get_libros(request, categoria: Optional[int] = None, buscar: Optional[str] = None):
    # ✅ Obtener usuario si está autenticado
    user = request.auth if hasattr(request, 'auth') else None
    return listar_libros(categoria=categoria, buscar=buscar, user=user)
# views.py - Asegurar que get_libros pase user correctamente

@router.get("/libros", tags=["Listar Libros Públicos"], response=list[LibroListOut])
@paginate
def get_libros(request, categoria: Optional[int] = None, buscar: Optional[str] = None):
    # ✅ Obtener usuario si está autenticado
    user = request.auth if hasattr(request, 'auth') else None
    return listar_libros(categoria=categoria, buscar=buscar, user=user)

@router.get("/libros/mios", tags=["Listar Mis Libros"], response=list[LibroListOut], auth=auth)
@paginate
def get_mis_libros(request):
    return listar_mis_libros(request.auth)

# ✅ MODIFICADO: Ahora incluye información del usuario autenticado
@router.get("/libros/{libro_id}", tags=["Obtener Libro por ID"], response=LibroOut)
def get_libro(request, libro_id: int):
    # ✅ MODIFICADO: Pasamos el usuario si está autenticado
    return obtener_libro(libro_id, user=request.auth if hasattr(request, 'auth') else None)


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


# ✅ NUEVO: Endpoint para obtener mi reseña
@router.get("/libros/{libro_id}/mi-resena", tags=["Mi Reseña"], response=Optional[ResenaOut], auth=auth)
def get_mi_resena(request, libro_id: int):
    """Obtener la reseña del usuario autenticado para este libro"""
    from .models import Resena  # Import aquí para evitar circular
    resena = Resena.objects.filter(libro_id=libro_id, usuario=request.auth).first()
    return resena


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


# views.py - Agregar al final de la sección de capítulos

# views.py - Agregar después de delete_capitulo
# ✅ REORDENAR CAPÍTULOS
@router.post(
    "/libros/{libro_id}/reordenar-capitulos",
    tags=["Reordenar Capítulos"],
    response=dict,
    auth=auth
)
def reordenar_capitulos_endpoint(request, libro_id: int, data: ReordenCapitulos):
    """
    Reordenar capítulos de un libro
    
    Envía la lista de IDs en el nuevo orden.
    Ejemplo: {"capitulos": [3, 2, 1]}
    """
    return reordenar_capitulos(libro_id, request.auth, data.capitulos)


# ✅ NUEVO: Auto-guardar capítulo
@router.post(
    "/libros/{libro_id}/capitulos/{numero}/auto-guardar",
    tags=["Auto-guardar Capítulo"],
    response=dict,
    auth=auth
)
def auto_guardar_capitulo(request, libro_id: int, numero: int, data: AutoGuardarCapitulo):
    """Auto-guardar un capítulo con historial de versiones"""
    from .models import Libro, Capitulo, LimiteEdicionDiario, VersionCapitulo
    
    capitulo = get_object_or_404(Capitulo, libro_id=libro_id, numero=numero)
    
    # Verificar permisos
    if capitulo.libro.autor != request.auth:
        raise PermissionDenied("No eres el autor de este libro")
    
    # Verificar límite diario de ediciones (anti-spam)
    limite, _ = LimiteEdicionDiario.objects.get_or_create(
        usuario=request.auth,
        fecha=date.today()
    )
    if limite.contador >= 100:  # 100 ediciones por día
        return 429, {"error": "Límite diario de ediciones alcanzado"}
    
    # Guardar versión anterior si hay cambios
    if capitulo.contenido != data.contenido:
        # Crear versión
        VersionCapitulo.objects.create(
            capitulo=capitulo,
            contenido=capitulo.contenido,
            usuario=request.auth,
            notas="Auto-guardado"
        )
        
        # Sanitizar y guardar nuevo contenido
        contenido_sanitizado = sanitizar_contenido_tiptap(data.contenido)
        capitulo.contenido = contenido_sanitizado
        capitulo.save()
        
        # Incrementar contador de límite
        limite.contador += 1
        limite.save()
        
        return 200, {"mensaje": "Guardado automático exitoso", "version_guardada": True}
    
    return 200, {"mensaje": "Sin cambios", "version_guardada": False}


# ✅ NUEVO: Obtener versiones de un capítulo
@router.get(
    "/libros/{libro_id}/capitulos/{numero}/versiones",
    tags=["Versiones de Capítulo"],
    response=list[VersionCapituloOut],
    auth=auth
)
def get_versiones_capitulo(request, libro_id: int, numero: int):
    """Obtener historial de versiones de un capítulo"""
    from .models import Capitulo, VersionCapitulo
    
    capitulo = get_object_or_404(Capitulo, libro_id=libro_id, numero=numero)
    
    # Verificar permisos
    if capitulo.libro.autor != request.auth:
        raise PermissionDenied("No eres el autor de este libro")
    
    return capitulo.versiones.all()[:50]  # Últimas 50 versiones


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


# ════════════════════════════════════════════════════════════
# ✅ NUEVOS ENDPOINTS (Agregar al final del archivo)
# ════════════════════════════════════════════════════════════

# ── Favoritos ──────────────────────────────────

@router.post("/libros/{libro_id}/favorito", tags=["Favoritos"], response=dict, auth=auth)
def toggle_favorito(request, libro_id: int):
    """Agregar o quitar libro de favoritos"""
    from .models import Libro
    
    libro = get_object_or_404(Libro, id=libro_id)
    
    # Solo se pueden marcar como favoritos libros públicos
    if libro.visibilidad != "publico":
        return 400, {"error": "Solo puedes agregar a favoritos libros públicos"}
    
    if libro in request.auth.libros_favoritos.all():
        request.auth.libros_favoritos.remove(libro)
        mensaje = "Eliminado de favoritos"
        es_favorito = False
    else:
        request.auth.libros_favoritos.add(libro)
        mensaje = "Agregado a favoritos"
        es_favorito = True
    
    return 200, {"mensaje": mensaje, "es_favorito": es_favorito}


@router.get("/me/favoritos", response=list[FavoritoOut], auth=auth)
def get_favoritos(request):
    """Obtener todos los libros favoritos del usuario"""
    return listar_favoritos(request.auth)


# ── Progreso de Lectura ──────────────────────

@router.post("/libros/{libro_id}/progreso", tags=["Progreso"], response=ProgresoOut, auth=auth)
def actualizar_progreso(request, libro_id: int, data: ProgresoIn):
    """Actualizar el progreso de lectura de un libro"""
    from .models import Libro, Capitulo, ProgresoLectura
    
    libro = get_object_or_404(Libro, id=libro_id)
    
    # Solo libros públicos o del autor
    if libro.visibilidad != "publico" and libro.autor != request.auth:
        raise PermissionDenied("No tienes acceso a este libro")
    
    progreso, created = ProgresoLectura.objects.get_or_create(
        usuario=request.auth,
        libro=libro
    )
    
    if data.capitulo_id:
        capitulo = get_object_or_404(Capitulo, id=data.capitulo_id, libro=libro)
        progreso.capitulo_actual = capitulo
        # Calcular porcentaje basado en capítulos
        total_capitulos = libro.capitulos.count()
        if total_capitulos > 0:
            progreso.porcentaje = int((capitulo.numero / total_capitulos) * 100)
    
    if data.pagina is not None:
        progreso.pagina = data.pagina
    
    if data.porcentaje and data.porcentaje > progreso.porcentaje:
        progreso.porcentaje = data.porcentaje
    
    progreso.save()
    return progreso


@router.get("/libros/{libro_id}/progreso", tags=["Progreso"], response=Optional[ProgresoOut], auth=auth)
def get_progreso(request, libro_id: int):
    """Obtener el progreso de lectura de un libro"""
    from .models import ProgresoLectura
    
    progreso = ProgresoLectura.objects.filter(
        usuario=request.auth,
        libro_id=libro_id
    ).first()
    
    return progreso


@router.get("/me/progresos", tags=["Progreso"], response=list[ProgresoOut], auth=auth)
def get_mis_progresos(request):
    """Obtener todos los progresos de lectura del usuario"""
    from .models import ProgresoLectura
    
    return ProgresoLectura.objects.filter(usuario=request.auth)


# ── Estadísticas ──────────────────────────────


@router.get("/me/estadisticas", tags=["Estadísticas"], response=dict, auth=auth)
def get_mis_estadisticas(request):
    from .models import Libro, Resena, Comentario
    
    total_libros = Libro.objects.filter(autor=request.auth).count()
    total_resenas = Resena.objects.filter(usuario=request.auth).count()
    total_comentarios = Comentario.objects.filter(usuario=request.auth).count()
    total_favoritos = request.auth.libros_favoritos.count()
    libros_publicados = Libro.objects.filter(autor=request.auth, visibilidad="publico").count()
    libros_privados = Libro.objects.filter(autor=request.auth, visibilidad="privado").count()
    
    return {
        "total_libros": total_libros,
        "total_resenas": total_resenas,
        "total_comentarios": total_comentarios,
        "total_favoritos": total_favoritos,
        "libros_publicados": libros_publicados,
        "libros_privados": libros_privados,
    }


@router.get("/libros/{libro_id}/estadisticas", tags=["Estadísticas"], response=dict)
def get_libro_estadisticas(request, libro_id: int):
    """Obtener estadísticas de un libro"""
    user = request.auth if hasattr(request, 'auth') else None
    return obtener_estadisticas_libro(libro_id, user)

# ── Límites de Edición ────────────────────────

@router.get("/me/limites-edicion", tags=["Límites"], response=dict, auth=auth)
def get_mis_limites_edicion(request):
    """Obtener límites de edición del usuario"""
    from .models import LimiteEdicionDiario
    
    limite, _ = LimiteEdicionDiario.objects.get_or_create(
        usuario=request.auth,
        fecha=date.today()
    )
    
    return {
        "fecha": limite.fecha,
        "contador": limite.contador,
        "limite_diario": 100,
        "restantes": 100 - limite.contador
    }
    


@router.get("/me/notificaciones", tags=["Notificaciones"], response=list[NotificacionOut], auth=auth)
def listar_notificaciones(request):
    """Obtener notificaciones del usuario autenticado (últimas 50)"""
    return obtener_notificaciones(request.auth)


@router.get("/me/notificaciones/no-leidas", tags=["Notificaciones"], response=int, auth=auth)
def contar_no_leidas(request):
    """Obtener cantidad de notificaciones no leídas del usuario"""
    return contar_notificaciones_no_leidas(request.auth)


@router.post("/me/notificaciones/marcar-leidas", tags=["Notificaciones"], response=dict, auth=auth)
def marcar_todas_leidas(request):
    """Marcar todas las notificaciones del usuario como leídas"""
    cantidad = marcar_notificaciones_leidas(request.auth)
    return {"mensaje": f"{cantidad} notificaciones marcadas como leídas"}


@router.post("/me/notificaciones/{notificacion_id}/leer", tags=["Notificaciones"], response=dict, auth=auth)
def marcar_una_leida(request, notificacion_id: int):
    """Marcar una notificación específica como leída"""
    marcar_notificacion_leida(notificacion_id, request.auth)
    return {"mensaje": "Notificación marcada como leída"}


@router.delete("/me/notificaciones/{notificacion_id}", tags=["Notificaciones"], auth=auth)
def eliminar_una_notificacion(request, notificacion_id: int):
    """Eliminar una notificación específica"""
    return eliminar_notificacion(notificacion_id, request.auth)


@router.delete("/me/notificaciones", tags=["Notificaciones"], auth=auth)
def eliminar_todas_notificaciones_view(request):
    """Eliminar todas las notificaciones del usuario"""
    return eliminar_todas_notificaciones(request.auth)