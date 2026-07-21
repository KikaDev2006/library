# models.py - VERSIÓN ACTUALIZADA COMPLETA

# models.py
from django.db import models
from django.conf import settings
from imagekit.models import ImageSpecField  # 👈 NUEVA IMPORTACIÓN
from imagekit.processors import ResizeToFit, ResizeToFill  # 👈 NUEVA IMPORTACIÓN


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
    
    # 👇 VERSIONES OPTIMIZADAS DE LA PORTADA (agrega esto)
    portada_thumb = ImageSpecField(
        source='portada',
        processors=[ResizeToFit(200, 300)],  # Para listas y tarjetas pequeñas
        format='WEBP',
        options={'quality': 70}
    )
    
    portada_medium = ImageSpecField(
        source='portada',
        processors=[ResizeToFit(400, 600)],  # Para tarjetas medianas
        format='WEBP',
        options={'quality': 75}
    )
    
    portada_large = ImageSpecField(
        source='portada',
        processors=[ResizeToFit(800, 1200)],  # Para vista detallada
        format='WEBP',
        options={'quality': 80}
    )
    
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
    
    favoritos = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="libros_favoritos",
        blank=True
    )

    def __str__(self):
        return self.titulo
    
    # 👇 MÉTODO PARA OBTENER URL SEGÚN TAMAÑO (opcional, pero útil)
    def get_portada_url(self, size='medium'):
        if not self.portada:
            return None
        if size == 'thumb':
            return self.portada_thumb.url
        elif size == 'large':
            return self.portada_large.url
        return self.portada_medium.url  # default


# ... resto de tus modelos (Capitulo, Resena, etc.) sin cambios


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


# ✅ NUEVOS MODELOS:

class ProgresoLectura(models.Model):
    """Progreso de lectura del usuario en un libro"""
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name="progresos"
    )
    libro = models.ForeignKey(
        Libro, 
        on_delete=models.CASCADE, 
        related_name="progresos"
    )
    capitulo_actual = models.ForeignKey(
        Capitulo, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name="progresos"
    )
    pagina = models.PositiveIntegerField(default=0)  # Para libros tipo "subido"
    ultima_lectura = models.DateTimeField(auto_now=True)
    porcentaje = models.PositiveSmallIntegerField(default=0)  # 0-100

    class Meta:
        unique_together = ["usuario", "libro"]
        ordering = ["-ultima_lectura"]

    def __str__(self):
        return f"{self.usuario} - {self.libro} ({self.porcentaje}%)"


class VersionCapitulo(models.Model):
    """Historial de versiones de un capítulo (para auto-guardado)"""
    capitulo = models.ForeignKey(
        Capitulo, 
        on_delete=models.CASCADE, 
        related_name="versiones"
    )
    contenido = models.TextField()
    fecha_version = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="versiones_capitulos"
    )
    notas = models.CharField(max_length=255, blank=True, null=True)  # Ej: "Auto-guardado", "Guardado manual"

    class Meta:
        ordering = ["-fecha_version"]

    def __str__(self):
        return f"{self.capitulo} - {self.fecha_version.strftime('%Y-%m-%d %H:%M')}"


class LimiteEdicionDiario(models.Model):
    """Límite de ediciones por usuario por día (anti-spam)"""
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="limites_edicion"
    )
    fecha = models.DateField(auto_now_add=True)
    contador = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ["usuario", "fecha"]
        
# libros/models.py - Agregar al final

class Notificacion(models.Model):
    """
    Modelo para notificaciones de libros públicos
    """
    TIPO_CHOICES = [
        ('nuevo_libro_publico', 'Nuevo libro público'),
        ('libro_actualizado', 'Libro actualizado'),
    ]
    
    # Usuario que recibe la notificación
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notificaciones'
    )
    
    # Tipo de notificación
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES)
    
    # Mensaje completo (ej: "El libro 'La luna de miel' fue creado por Erika")
    mensaje = models.TextField()
    
    # Datos específicos del libro
    libro_id = models.IntegerField()
    titulo_libro = models.CharField(max_length=255)
    autor_nombre = models.CharField(max_length=150)
    autor_id = models.IntegerField()
    
    # Estado
    leida = models.BooleanField(default=False)
    
    # Fecha
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['usuario', 'leida']),
            models.Index(fields=['-fecha_creacion']),
        ]
    
    def __str__(self):
        return f"{self.usuario.username} - {self.tipo} - {self.titulo_libro}"