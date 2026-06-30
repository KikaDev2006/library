# mi_api/api.py
from ninja import NinjaAPI
from usuarios.views import router as usuarios_router

api = NinjaAPI(title="Mi API de Usuarios", version="1.0.0")
api.add_router("/usuarios", usuarios_router)

# Expose OpenAPI JSON and docs URLs under /api/ by wiring in urls.py
