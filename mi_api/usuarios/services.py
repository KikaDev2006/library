import datetime
from types import SimpleNamespace
from libros.models import Libro
import jwt
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password
from django.shortcuts import get_object_or_404
from ninja.errors import HttpError
from django.db import IntegrityError
from .models import TokenBlacklist, Usuario



def crear_usuario(data):
    try:
        user = Usuario.objects.create(
            email=data.email,
            username=data.username
        )
    except IntegrityError:
        raise HttpError(400, "Ya existe un usuario con ese email o nombre de usuario")

    user.set_password(data.password)
    user.save()
    return user


def listar_usuarios():
    return Usuario.objects.filter(is_active=True)


def obtener_usuario_por_id(user_id: int):
    return get_object_or_404(Usuario, id=user_id, is_active=True)


def login_usuario(email: str, password: str):
    user = authenticate(username=email, password=password)
    if not user:
        raise HttpError(401, "Credenciales inválidas")

    payload = {
        "id": user.id,
        "email": user.email,
        "iat": datetime.datetime.utcnow(),
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1),
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
    return {"token": token}


def logout_user(token: str):
    TokenBlacklist.objects.get_or_create(token=token)
    return {"message": "Logout exitoso"}


def update_user(request_user, user_id: int, data: dict, imagen=None, eliminar_imagen=False):
    if request_user.id != user_id and not request_user.is_staff:
        raise HttpError(403, "No tenés permiso para editar este usuario")

    try:
        usuario = Usuario.objects.get(id=user_id)
    except Usuario.DoesNotExist:
        raise HttpError(404, "Usuario no encontrado")

    if data.get("username"):
        usuario.username = data["username"]

    if data.get("email"):
        usuario.email = data["email"]

    if data.get("password"):
        usuario.password = make_password(data["password"])

    if eliminar_imagen:
        usuario.imagen.delete(save=False)
        usuario.imagen = None
    elif imagen:
        usuario.imagen = imagen

    usuario.save()
    return usuario

def eliminar_usuario(request_user, user_id):
    if request_user.id != user_id and not request_user.is_staff:
        raise HttpError(403, "No tenés permiso para eliminar este usuario")

    try:
        usuario = Usuario.objects.get(id=user_id)
    except Usuario.DoesNotExist:
        raise HttpError(404, "Usuario no encontrado")

    usuario.is_active = False
    usuario.save()
    return {"message": "Usuario eliminado correctamente"}


def buscar_usuarios(q: str):
    if not q or not q.strip():
        return Usuario.objects.none()
    return Usuario.objects.filter(
        username__icontains=q.strip(), is_active=True
    )[:20]


def obtener_perfil_publico(username: str):
    try:
        usuario = Usuario.objects.get(username=username, is_active=True)
    except Usuario.DoesNotExist:
        raise HttpError(404, "Usuario no encontrado")

    libros = (
        Libro.objects.filter(autor=usuario, visibilidad="publico")
        .prefetch_related("categorias")
        .order_by("-fecha_creacion")
    )

    grupos: dict[int, dict] = {}
    orden_categorias: list[int] = []
    sin_categoria: list = []

    for libro in libros:
        categorias_libro = list(libro.categorias.all())
        if not categorias_libro:
            sin_categoria.append(libro)
            continue
        primera = categorias_libro[0]
        if primera.id not in grupos:
            grupos[primera.id] = {"categoria": primera, "libros": []}
            orden_categorias.append(primera.id)
        grupos[primera.id]["libros"].append(libro)

    categorias_resultado = [grupos[cid] for cid in orden_categorias]

    if sin_categoria:
        categoria_otros = SimpleNamespace(id=0, nombre="Otros", descripcion=None)
        categorias_resultado.append({"categoria": categoria_otros, "libros": sin_categoria})

    usuario.categorias = categorias_resultado
    return usuario

def actualizar_config_notificaciones(usuario, activas: bool):
    usuario.notificaciones_activas = activas
    usuario.save()
    return usuario