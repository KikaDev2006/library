# mi_api/api.py
from ninja import NinjaAPI
from usuarios.views import public_router, private_router

api = NinjaAPI(title="Mi API de Usuarios", version="1.0.0")

api.add_router("/public", public_router)
api.add_router("/usuarios", private_router)

