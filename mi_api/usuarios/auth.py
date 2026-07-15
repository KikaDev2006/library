# mi_api/auth.py
import jwt
from django.conf import settings
from ninja.security import HttpBearer
from usuarios.models import Usuario, TokenBlacklist


class JWTAuth(HttpBearer):
    def authenticate(self, request, token):
        # 👇 si el token fue invalidado por logout, se rechaza
        if TokenBlacklist.objects.filter(token=token).exists():
            return None

        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            user = Usuario.objects.get(id=payload["id"])
            return user
        except Exception:
            return None