# mi_api/api.py
from ninja import NinjaAPI
from usuarios.views import router as usuarios_router

api = NinjaAPI()
api.add_router("/usuarios", usuarios_router)
