

from .schemas import UsuarioIn, UsuarioOut
from .services import crear_usuario, listar_usuarios, obtener_usuario_por_id
from ninja import Router
from .auth import JWTAuth
import jwt
from django.conf import settings
from django.contrib.auth import authenticate

public_router = Router()
@public_router.post("/usuarios",tags=["Crear Usuarios"], response=UsuarioOut)
def registro_usuario(request, data: UsuarioIn):
    user = crear_usuario(data)
    return user
@public_router.post("/login", tags=["Login de Usuario"])
def login(request, email: str, password: str):
    user = authenticate(username=email, password=password)
    if user:
        payload = {"id": user.id, "email": user.email}
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
        return {"token": token}
    return {"error": "Credenciales inválidas"}

@public_router.get("/usuarios", tags=["Obtener Usuarios"], response=list[UsuarioOut])
def obtener_usuarios(request):
    return listar_usuarios()
@public_router.get("/{user_id}", tags=["Obtener Usuario por ID"], response=UsuarioOut)
def obtener_usuario(request, user_id: int):
    return obtener_usuario_por_id(user_id)


private_router = Router(auth=JWTAuth())
@private_router.get("/me", tags=["Obtener Información del Usuario Autenticado"])
def me(request):
    user = request.auth
    return {"id": user.id, "email": user.email}