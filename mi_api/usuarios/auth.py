import jwt
from django.conf import settings
from ninja.security import HttpBearer
from usuarios.models import Usuario, TokenBlacklist

COOKIE_NAME = "access_token"


class JWTAuth(HttpBearer):
    def authenticate(self, request, token):
        return self._validate(token)

    # HttpBearer solo llama a authenticate() cuando encuentra un header
    # "Authorization: Bearer ...". Sobreescribimos __call__ para intentar
    # primero la cookie httpOnly (usada por el middleware de Next.js) y,
    # si no hay o es inválida, caer al flujo normal de Bearer header
    # (el que sigue usando el frontend para las llamadas fetch normales).
    def __call__(self, request):
        cookie_token = request.COOKIES.get(COOKIE_NAME)
        if cookie_token:
            user = self._validate(cookie_token)
            if user:
                return user
        return super().__call__(request)

    def _validate(self, token):
        if not token:
            return None
        # 👇 si el token fue invalidado por logout, se rechaza
        if TokenBlacklist.objects.filter(token=token).exists():
            return None

        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            user = Usuario.objects.get(id=payload["id"])
            return user
        except Exception:
            return None