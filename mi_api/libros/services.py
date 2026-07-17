from django.db.models import Avg, Q
from ninja.errors import HttpError

from .models import Categoria, Capitulo, Comentario, Libro, Resena


# ── Categorías ──────────────────────────────────

def listar_categorias():
    return Categoria.objects.all()



# ── Libros ──────────────────────────────────────

def _con_promedio(queryset):
    return queryset.annotate(promedio_puntuacion=Avg("resenas__puntuacion"))


def listar_libros(categoria: int | None = None, buscar: str | None = None):
    qs = Libro.objects.filter(visibilidad="publico")

    if categoria:
        qs = qs.filter(categorias__id=categoria)

    if buscar:
        qs = qs.filter(
            Q(titulo__icontains=buscar) | Q(descripcion__icontains=buscar)
        )

    return _con_promedio(qs).distinct().order_by("-fecha_creacion")


def listar_mis_libros(usuario):
    qs = Libro.objects.filter(autor=usuario)
    return _con_promedio(qs).order_by("-fecha_creacion")


def obtener_libro(libro_id: int, request_user=None):
    try:
        libro = _con_promedio(Libro.objects.filter(id=libro_id)).get()
    except Libro.DoesNotExist:
        raise HttpError(404, "Libro no encontrado")

    if libro.visibilidad == "privado":
        if request_user is None or libro.autor_id != request_user.id:
            raise HttpError(404, "Libro no encontrado")

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