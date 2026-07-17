from typing import Annotated, Optional

from ninja import File, Form, Router, UploadedFile

from .auth import JWTAuth
from .schemas import (
    LoginOut,
    TokenOut,
    UsuarioIn,
    UsuarioOut,
    UsuarioPublicOut,
    UsuarioUpdate,
)
from .services import (
    crear_usuario,
    eliminar_usuario,
    listar_usuarios,
    login_usuario,
    logout_user,
    obtener_usuario_por_id,
    update_user,
)

public_router = Router()


@public_router.post("/usuarios", tags=["Crear Usuarios"], response=UsuarioOut)
def registro_usuario(request, data: UsuarioIn):
    return crear_usuario(data)


@public_router.post("/login", tags=["Login de Usuario"], response=TokenOut)
def login(request, email: str, password: str):
    return login_usuario(email, password)


@public_router.get("/usuarios", tags=["Obtener Usuarios"], response=list[UsuarioPublicOut])
def obtener_usuarios(request):
    return listar_usuarios()


@public_router.get("/{user_id}", tags=["Obtener Usuario por ID"], response=UsuarioPublicOut)
def obtener_usuario(request, user_id: int):
    return obtener_usuario_por_id(user_id)


private_router = Router(auth=JWTAuth())


@private_router.post("/logout", tags=["Logout"], response=LoginOut)
def logout(request):
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    return logout_user(token)


@private_router.get("/me", tags=["Obtener Información del Usuario Autenticado"], response=UsuarioOut)
def me(request):
    return request.auth


@private_router.put("/{user_id}", tags=["Actualizar Usuario"], response=UsuarioOut)
def update_user_view(
    request,
    user_id: int,
    username: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    password: Optional[str] = Form(None),
    imagen: Annotated[Optional[UploadedFile], File()] = None,
    eliminar_imagen: Optional[bool] = Form(False),
):
    data = {
        "username": username,
        "email": email,
        "password": password,
    }
    return update_user(request.auth, user_id, data, imagen, eliminar_imagen)


@private_router.delete("/{user_id}", tags=["Eliminar Usuario"], response=LoginOut)
def eliminar_usuario_view(request, user_id: int):
    return eliminar_usuario(request.auth, user_id)