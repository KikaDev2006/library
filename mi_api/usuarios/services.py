import datetime

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


def update_user(request_user, user_id: int, data: dict, imagen=None):
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

    if imagen:
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