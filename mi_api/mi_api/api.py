from ninja import NinjaAPI

from usuarios.views import public_router as usuarios_public_router
from usuarios.views import private_router as usuarios_private_router
from libros.views import router as libros_router

api = NinjaAPI(title="Mi API de Usuarios", version="1.0.0")

api.add_router("/public", usuarios_public_router)
api.add_router("/usuarios", usuarios_private_router)

api.add_router("", libros_router)