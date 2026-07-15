from .models import Usuario
from django.shortcuts import get_object_or_404
from django.contrib.auth import authenticate
import jwt
from django.conf import settings

from django.contrib.auth.hashers import make_password
from usuarios.models import Usuario

def crear_usuario(data):
    user = Usuario.objects.create(
        email=data.email,
        username=data.username
    )
    user.set_password(data.password)  # 👈 encripta y guarda en el campo correcto
    user.save()
       
    
    return user

def listar_usuarios():
    return Usuario.objects.all()

def obtener_usuario_por_id(user_id: int):
    return get_object_or_404(Usuario, id=user_id)

SECRET = settings.SECRET_KEY

def login_usuario(email: str, password: str):
    # Si tu modelo usa email como USERNAME_FIELD, puedes pasar email como username
    user = authenticate(username=email, password=password)
    if user:
        payload = {"id": user.id, "email": user.email}
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
        return {"token": token}
    return {"error": "Credenciales inválidas"}