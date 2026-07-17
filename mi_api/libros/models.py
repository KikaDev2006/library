from django.db import models
from django.conf import settings


class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nombre


class Libro(models.Model):
    TIPO_CHOICES = [
        ("escrito", "Escrito en la plataforma"),
        ("subido", "Archivo subido"),
    ]
    VISIBILIDAD_CHOICES = [
        ("publico", "Público"),
        ("privado", "Privado"),
    ]

    titulo = models.CharField(max_length=255)
    portada = models.ImageField(upload_to="libros/portadas/", blank=True, null=True)
    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="libros",
    )
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    archivo = models.FileField(upload_to="libros/archivos/", blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True)
    categorias = models.ManyToManyField(Categoria, related_name="libros", blank=True)
    paginas = models.PositiveIntegerField(blank=True, null=True)
    fecha_publicacion = models.DateField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    visibilidad = models.CharField(
        max_length=10, choices=VISIBILIDAD_CHOICES, default="privado"
    )

    def __str__(self):
        return self.titulo


class Capitulo(models.Model):
    libro = models.ForeignKey(Libro, on_delete=models.CASCADE, related_name="capitulos")
    numero = models.PositiveIntegerField()
    titulo = models.CharField(max_length=255)
    contenido = models.TextField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("libro", "numero")
        ordering = ["numero"]

    def __str__(self):
        return f"{self.libro.titulo} — Cap. {self.numero}: {self.titulo}"


class Resena(models.Model):
    libro = models.ForeignKey(Libro, on_delete=models.CASCADE, related_name="resenas")
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="resenas"
    )
    puntuacion = models.PositiveSmallIntegerField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("libro", "usuario")

    def __str__(self):
        return f"{self.usuario} → {self.libro} ({self.puntuacion})"


class Comentario(models.Model):
    libro = models.ForeignKey(Libro, on_delete=models.CASCADE, related_name="comentarios")
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="comentarios"
    )
    texto = models.TextField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha_creacion"]

    def __str__(self):
        return f"{self.usuario} en {self.libro}"