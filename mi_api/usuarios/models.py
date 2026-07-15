from django.db import models
from django.contrib.auth.models import AbstractUser

class Usuario(AbstractUser):
    
    imagen = models.ImageField(upload_to="usuarios/", blank=True, null=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    # ⚡️ email único
    email = models.EmailField(unique=True)

    # ⚡️ aquí está la lógica clave:
    USERNAME_FIELD = "email"          # el campo usado para login será email
    REQUIRED_FIELDS = ["username"]    # username sigue existiendo, pero no es el login
