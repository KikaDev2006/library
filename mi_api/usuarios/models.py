from django.db import models

# Create your models here.
class Usuario(models.Model):
    nombre = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    contraseña = models.CharField(max_length=100)
    imagen = models.ImageField(upload_to='usuarios/', blank=True, null=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)