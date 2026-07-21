from django.db.models import Avg, Q, Max 
from ninja.errors import HttpError
from django.db import transaction
from datetime import date

from .models import (
    Categoria, 
    Capitulo, 
    Comentario, 
    Libro, 
    Resena,
    ProgresoLectura,
    VersionCapitulo,
    LimiteEdicionDiario,
    Notificacion,
)
from django.contrib.auth import get_user_model
User = get_user_model()

# ── Categorías ──────────────────────────────────

def listar_categorias():
    return Categoria.objects.all()


# ── Libros ──────────────────────────────────────

def _con_promedio(queryset):
    return queryset.annotate(promedio_puntuacion=Avg("resenas__puntuacion"))


# services.py - Versión completa con user

def listar_libros(categoria: int | None = None, buscar: str | None = None, user=None):
    """
    Listar libros públicos con filtros opcionales
    """
    qs = Libro.objects.filter(visibilidad="publico")

    if categoria:
        qs = qs.filter(categorias__id=categoria)

    if buscar:
        qs = qs.filter(
            Q(titulo__icontains=buscar) | Q(descripcion__icontains=buscar)
        )

    # Anotar promedio
    qs = _con_promedio(qs)
    
    # ✅ Si hay usuario, añadir información de favoritos
    if user:
        qs = qs.prefetch_related('categorias')
        # Obtener IDs de favoritos del usuario
        favoritos_ids = user.libros_favoritos.values_list('id', flat=True)
        # Añadir campo es_favorito a cada libro (se maneja en serialización)
        for libro in qs:
            libro.es_favorito = libro.id in favoritos_ids

    return qs.distinct().order_by("-fecha_creacion")


def listar_mis_libros(usuario):
    qs = Libro.objects.filter(autor=usuario)
    return _con_promedio(qs).order_by("-fecha_creacion")


def obtener_libro(libro_id: int, user=None):
    """
    Obtener un libro por ID con información personalizada del usuario
    """
    try:
        libro = _con_promedio(Libro.objects.filter(id=libro_id)).get()
    except Libro.DoesNotExist:
        raise HttpError(404, "Libro no encontrado")

    # Verificar acceso a libros privados
    if libro.visibilidad == "privado":
        if user is None or libro.autor_id != user.id:
            raise HttpError(404, "Libro no encontrado")

    # Agregar información personalizada del usuario autenticado
    if user:
        # Mi puntuación
        resena = Resena.objects.filter(libro=libro, usuario=user).first()
        libro.mi_puntuacion = resena.puntuacion if resena else None
        libro.mi_resena_id = resena.id if resena else None
        
        # Es favorito
        libro.es_favorito = libro in user.libros_favoritos.all()

    return libro
 

def crear_libro(usuario, data, portada=None, archivo=None):
    if data.tipo == "subido" and not archivo:
        raise HttpError(400, "Debés subir un archivo para libros de tipo 'subido'")

    libro = Libro.objects.create(
        titulo=data.titulo,
        tipo=data.tipo,
        descripcion=data.descripcion,
        paginas=data.paginas,
        fecha_publicacion=data.fecha_publicacion,
        visibilidad=data.visibilidad,
        autor=usuario,
        portada=portada,
        archivo=archivo if data.tipo == "subido" else None,
    )

    if data.categorias:
        categorias = Categoria.objects.filter(id__in=data.categorias)
        libro.categorias.set(categorias)

    return _con_promedio(Libro.objects.filter(id=libro.id)).get()


def _validar_dueno(libro, request_user):
    if libro.autor_id != request_user.id and not request_user.is_staff:
        raise HttpError(403, "No tenés permiso para modificar este libro")


def actualizar_libro(libro_id: int, request_user, data, portada=None):
    try:
        libro = Libro.objects.get(id=libro_id)
    except Libro.DoesNotExist:
        raise HttpError(404, "Libro no encontrado")

    _validar_dueno(libro, request_user)

    if data.titulo is not None:
        libro.titulo = data.titulo
    if data.descripcion is not None:
        libro.descripcion = data.descripcion
    if data.paginas is not None:
        libro.paginas = data.paginas
    if data.fecha_publicacion is not None:
        libro.fecha_publicacion = data.fecha_publicacion
    if data.visibilidad is not None:
        if data.visibilidad not in ("publico", "privado"):
            raise HttpError(400, "visibilidad debe ser 'publico' o 'privado'")
        libro.visibilidad = data.visibilidad
    if portada is not None:
        libro.portada = portada

    libro.save()

    if data.categorias is not None:
        categorias = Categoria.objects.filter(id__in=data.categorias)
        libro.categorias.set(categorias)

    return _con_promedio(Libro.objects.filter(id=libro.id)).get()


def eliminar_libro(libro_id: int, request_user):
    try:
        libro = Libro.objects.get(id=libro_id)
    except Libro.DoesNotExist:
        raise HttpError(404, "Libro no encontrado")

    _validar_dueno(libro, request_user)
    libro.delete()
    return {"message": "Libro eliminado correctamente"}


# ── Capítulos ───────────────────────────────────

def listar_capitulos(libro_id: int, request_user=None):
    libro = obtener_libro(libro_id, request_user)
    return libro.capitulos.all()


def obtener_capitulo(libro_id: int, numero: int, request_user=None):
    libro = obtener_libro(libro_id, request_user)
    try:
        return libro.capitulos.get(numero=numero)
    except Capitulo.DoesNotExist:
        raise HttpError(404, "Capítulo no encontrado")


def crear_capitulo(libro_id: int, request_user, data):
    try:
        libro = Libro.objects.get(id=libro_id)
    except Libro.DoesNotExist:
        raise HttpError(404, "Libro no encontrado")

    _validar_dueno(libro, request_user)

    if libro.tipo != "escrito":
        raise HttpError(400, "Solo los libros de tipo 'escrito' pueden tener capítulos")

    if Capitulo.objects.filter(libro=libro, numero=data.numero).exists():
        raise HttpError(400, f"Ya existe el capítulo número {data.numero} en este libro")

    return Capitulo.objects.create(
        libro=libro,
        numero=data.numero,
        titulo=data.titulo,
        contenido=data.contenido,
    )


def actualizar_capitulo(capitulo_id: int, request_user, data):
    try:
        capitulo = Capitulo.objects.select_related("libro").get(id=capitulo_id)
    except Capitulo.DoesNotExist:
        raise HttpError(404, "Capítulo no encontrado")

    _validar_dueno(capitulo.libro, request_user)

    if data.numero is not None and data.numero != capitulo.numero:
        if Capitulo.objects.filter(libro=capitulo.libro, numero=data.numero).exists():
            raise HttpError(400, f"Ya existe el capítulo número {data.numero} en este libro")
        capitulo.numero = data.numero
    if data.titulo is not None:
        capitulo.titulo = data.titulo
    if data.contenido is not None:
        capitulo.contenido = data.contenido

    capitulo.save()
    return capitulo


def eliminar_capitulo(capitulo_id: int, request_user):
    try:
        capitulo = Capitulo.objects.select_related("libro").get(id=capitulo_id)
    except Capitulo.DoesNotExist:
        raise HttpError(404, "Capítulo no encontrado")

    _validar_dueno(capitulo.libro, request_user)
    capitulo.delete()
    return {"message": "Capítulo eliminado correctamente"}


# ── Reseñas ─────────────────────────────────────

def puntuar_libro(libro_id: int, usuario, data):
    try:
        libro = Libro.objects.get(id=libro_id)
    except Libro.DoesNotExist:
        raise HttpError(404, "Libro no encontrado")

    resena, _ = Resena.objects.update_or_create(
        libro=libro,
        usuario=usuario,
        defaults={"puntuacion": data.puntuacion},
    )
    return resena


def listar_resenas(libro_id: int):
    return Resena.objects.filter(libro_id=libro_id).select_related("usuario")


# ── Comentarios ─────────────────────────────────

def comentar_libro(libro_id: int, usuario, data):
    try:
        libro = Libro.objects.get(id=libro_id)
    except Libro.DoesNotExist:
        raise HttpError(404, "Libro no encontrado")

    return Comentario.objects.create(libro=libro, usuario=usuario, texto=data.texto)


def listar_comentarios(libro_id: int):
    return Comentario.objects.filter(libro_id=libro_id).select_related("usuario")


def eliminar_comentario(comentario_id: int, request_user):
    try:
        comentario = Comentario.objects.get(id=comentario_id)
    except Comentario.DoesNotExist:
        raise HttpError(404, "Comentario no encontrado")

    if comentario.usuario_id != request_user.id and not request_user.is_staff:
        raise HttpError(403, "No tenés permiso para eliminar este comentario")

    comentario.delete()
    return {"message": "Comentario eliminado correctamente"}


# ════════════════════════════════════════════════════════════
# ✅ NUEVAS FUNCIONALIDADES
# ════════════════════════════════════════════════════════════

# ── Favoritos ──────────────────────────────────

def toggle_favorito(libro_id: int, usuario):
    """Agregar o quitar libro de favoritos"""
    try:
        libro = Libro.objects.get(id=libro_id)
    except Libro.DoesNotExist:
        raise HttpError(404, "Libro no encontrado")

    if libro.visibilidad != "publico":
        raise HttpError(400, "Solo puedes agregar a favoritos libros públicos")

    if libro in usuario.libros_favoritos.all():
        usuario.libros_favoritos.remove(libro)
        return {"mensaje": "Eliminado de favoritos", "es_favorito": False}
    else:
        usuario.libros_favoritos.add(libro)
        return {"mensaje": "Agregado a favoritos", "es_favorito": True}


def listar_favoritos(usuario):
    """Listar libros favoritos del usuario"""
    return usuario.libros_favoritos.all()


# ── Progreso de Lectura ──────────────────────

def actualizar_progreso(libro_id: int, usuario, data):
    """Actualizar el progreso de lectura de un libro"""
    try:
        libro = Libro.objects.get(id=libro_id)
    except Libro.DoesNotExist:
        raise HttpError(404, "Libro no encontrado")

    # Verificar acceso
    if libro.visibilidad != "publico" and libro.autor != usuario:
        raise HttpError(403, "No tienes acceso a este libro")

    progreso, created = ProgresoLectura.objects.get_or_create(
        usuario=usuario,
        libro=libro
    )

    if data.capitulo_id:
        try:
            capitulo = Capitulo.objects.get(id=data.capitulo_id, libro=libro)
        except Capitulo.DoesNotExist:
            raise HttpError(404, "Capítulo no encontrado")
        
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


def obtener_progreso(libro_id: int, usuario):
    """Obtener el progreso de lectura de un libro"""
    try:
        return ProgresoLectura.objects.get(
            usuario=usuario,
            libro_id=libro_id
        )
    except ProgresoLectura.DoesNotExist:
        return None


def listar_mis_progresos(usuario):
    """Listar todos los progresos del usuario"""
    return ProgresoLectura.objects.filter(usuario=usuario)

def eliminar_progreso(libro_id: int, usuario):
    """Eliminar el progreso de lectura de un libro (quita el libro de la biblioteca)"""
    try:
        progreso = ProgresoLectura.objects.get(usuario=usuario, libro_id=libro_id)
    except ProgresoLectura.DoesNotExist:
        raise HttpError(404, "No tienes progreso registrado para este libro")

    progreso.delete()
    return {"message": "Libro eliminado de la biblioteca"}


# ── Versiones de Capítulos ────────────────────

def auto_guardar_capitulo(libro_id: int, numero: int, usuario, contenido: str):
    """Auto-guardar un capítulo con historial de versiones"""
    try:
        capitulo = Capitulo.objects.get(libro_id=libro_id, numero=numero)
    except Capitulo.DoesNotExist:
        raise HttpError(404, "Capítulo no encontrado")

    # Verificar permisos
    if capitulo.libro.autor != usuario:
        raise HttpError(403, "No eres el autor de este libro")

    # Verificar límite diario
    limite, _ = LimiteEdicionDiario.objects.get_or_create(
        usuario=usuario,
        fecha=date.today()
    )
    if limite.contador >= 100:
        raise HttpError(429, "Límite diario de ediciones alcanzado")

    # Guardar versión anterior si hay cambios
    if capitulo.contenido != contenido:
        VersionCapitulo.objects.create(
            capitulo=capitulo,
            contenido=capitulo.contenido,
            usuario=usuario,
            notas="Auto-guardado"
        )

        capitulo.contenido = contenido
        capitulo.save()

        limite.contador += 1
        limite.save()

        return {"mensaje": "Guardado automático exitoso", "version_guardada": True}

    return {"mensaje": "Sin cambios", "version_guardada": False}


def listar_versiones_capitulo(libro_id: int, numero: int, usuario):
    """Listar versiones de un capítulo"""
    try:
        capitulo = Capitulo.objects.get(libro_id=libro_id, numero=numero)
    except Capitulo.DoesNotExist:
        raise HttpError(404, "Capítulo no encontrado")

    if capitulo.libro.autor != usuario:
        raise HttpError(403, "No eres el autor de este libro")

    return capitulo.versiones.all()[:50]


# ── Reordenar Capítulos ──────────────────────



def reordenar_capitulos(libro_id: int, usuario, nuevos_ids: list[int]):
    """
    Reordenar capítulos de un libro usando números temporales grandes
    
    Estrategia:
    1. Asignar números temporales grandes (max_numero + 1000 + índice)
    2. Asignar los números correctos en el nuevo orden
    
    Esto evita conflictos UNIQUE y CHECK constraint en SQLite.
    
    Args:
        libro_id: ID del libro
        usuario: Usuario autenticado (debe ser el autor)
        nuevos_ids: Lista de IDs en el NUEVO orden
    
    Returns:
        dict: Mensaje de éxito
    
    Raises:
        HttpError: Si el usuario no es el autor o los IDs no son válidos
    """
    try:
        libro = Libro.objects.get(id=libro_id)
    except Libro.DoesNotExist:
        raise HttpError(404, "Libro no encontrado")

    # Verificar que el usuario sea el autor
    if libro.autor != usuario:
        raise HttpError(403, "No eres el autor de este libro")

    # Obtener TODOS los capítulos del libro
    capitulos = list(libro.capitulos.all())
    
    # Validar que la cantidad coincida
    if len(nuevos_ids) != len(capitulos):
        raise HttpError(
            400, 
            f"El número de capítulos no coincide. Esperados: {len(capitulos)}, Recibidos: {len(nuevos_ids)}"
        )

    # Validar que todos los IDs existen en el libro
    ids_actuales = [c.id for c in capitulos]
    if set(nuevos_ids) != set(ids_actuales):
        faltantes = set(ids_actuales) - set(nuevos_ids)
        extra = set(nuevos_ids) - set(ids_actuales)
        error_msg = "Los IDs de capítulos no son válidos"
        if faltantes:
            error_msg += f". Faltan: {list(faltantes)}"
        if extra:
            error_msg += f". Sobran: {list(extra)}"
        raise HttpError(400, error_msg)

    # Obtener el número máximo actual
    max_numero = libro.capitulos.aggregate(max_num=Max('numero'))['max_num'] or 0

    # Reordenar usando la estrategia de números temporales grandes
    with transaction.atomic():
        # PASO 1: Asignar números temporales grandes (positivos)
        # Ejemplo: max_numero + 1000 + 1 = 1004, 1005, 1006, ...
        # Esto evita conflictos UNIQUE y CHECK constraint
        for idx, capitulo_id in enumerate(nuevos_ids, 1):
            Capitulo.objects.filter(
                id=capitulo_id, 
                libro=libro
            ).update(numero=max_numero + 1000 + idx)
        
        # PASO 2: Asignar los números correctos en el nuevo orden
        for idx, capitulo_id in enumerate(nuevos_ids, 1):
            Capitulo.objects.filter(
                id=capitulo_id, 
                libro=libro
            ).update(numero=idx)

    return {
        "mensaje": "Capítulos reordenados exitosamente",
        "nuevo_orden": nuevos_ids,
        "total_capitulos": len(capitulos)
    }

# ── Estadísticas ──────────────────────────────

def obtener_estadisticas_usuario(usuario):
    """Obtener estadísticas del usuario autenticado"""
    total_libros = Libro.objects.filter(autor=usuario).count()
    total_resenas = Resena.objects.filter(usuario=usuario).count()
    total_comentarios = Comentario.objects.filter(usuario=usuario).count()
    total_favoritos = usuario.libros_favoritos.count()
    libros_publicados = Libro.objects.filter(autor=usuario, visibilidad="publico").count()
    libros_privados = Libro.objects.filter(autor=usuario, visibilidad="privado").count()

    return {
        "total_libros": total_libros,
        "total_resenas": total_resenas,
        "total_comentarios": total_comentarios,
        "total_favoritos": total_favoritos,
        "libros_publicados": libros_publicados,
        "libros_privados": libros_privados,
    }

# services.py - Función corregida
def obtener_estadisticas_libro(libro_id: int, usuario=None):
    """Obtener estadísticas de un libro"""
    try:
        libro = Libro.objects.get(id=libro_id)
    except Libro.DoesNotExist:
        raise HttpError(404, "Libro no encontrado")
    
    # Verificar acceso
    if libro.visibilidad == "privado":
        if not usuario or usuario != libro.autor:
            raise HttpError(403, "Este libro es privado")
    
    total_resenas = libro.resenas.count()
    
    # ✅ Usar Avg directamente (no models.Avg)
    promedio = libro.resenas.aggregate(promedio=Avg('puntuacion'))['promedio']
    
    total_comentarios = libro.comentarios.count()
    total_capitulos = libro.capitulos.count()
    
    # Número de lectores (solo si es público o eres el autor)
    total_lectores = None
    if libro.visibilidad == "publico" or (usuario and usuario == libro.autor):
        total_lectores = ProgresoLectura.objects.filter(libro=libro).count()
    
    return {
        "libro_id": libro_id,
        "titulo": libro.titulo,
        "visibilidad": libro.visibilidad,
        "total_resenas": total_resenas,
        "promedio_puntuacion": float(promedio) if promedio else None,
        "total_comentarios": total_comentarios,
        "total_capitulos": total_capitulos,
        "total_lectores": total_lectores,
    }

def obtener_limites_edicion(usuario):
    """Obtener límites de edición del usuario"""
    limite, _ = LimiteEdicionDiario.objects.get_or_create(
        usuario=usuario,
        fecha=date.today()
    )

    return {
        "fecha": limite.fecha,
        "contador": limite.contador,
        "limite_diario": 100,
        "restantes": 100 - limite.contador
    }
    


# ── Notificaciones ─────────────────────────────

def obtener_notificaciones(usuario):
    """
    Obtener notificaciones del usuario (últimas 50)
    """
    return Notificacion.objects.filter(usuario=usuario).order_by('-fecha_creacion')[:50]


def contar_notificaciones_no_leidas(usuario):
    """
    Contar notificaciones no leídas del usuario
    """
    return Notificacion.objects.filter(usuario=usuario, leida=False).count()


def marcar_notificaciones_leidas(usuario):
    """
    Marcar todas las notificaciones del usuario como leídas
    """
    return Notificacion.objects.filter(usuario=usuario, leida=False).update(leida=True)


def marcar_notificacion_leida(notificacion_id, usuario):
    """
    Marcar una notificación específica como leída
    """
    from django.shortcuts import get_object_or_404
    
    notificacion = get_object_or_404(Notificacion, id=notificacion_id, usuario=usuario)
    notificacion.leida = True
    notificacion.save()
    return notificacion


def eliminar_notificacion(notificacion_id, usuario):
    """
    Eliminar una notificación específica
    """
    from django.shortcuts import get_object_or_404
    
    notificacion = get_object_or_404(Notificacion, id=notificacion_id, usuario=usuario)
    notificacion.delete()
    return {"mensaje": "Notificación eliminada"}


def eliminar_todas_notificaciones(usuario):
    """
    Eliminar todas las notificaciones del usuario
    """
    count = Notificacion.objects.filter(usuario=usuario).delete()[0]
    return {"mensaje": f"{count} notificaciones eliminadas"}