# libros/apps.py

from django.apps import AppConfig


class LibrosConfig(AppConfig):
    name = 'libros'
    
    def ready(self):
        import libros.signals  # ← Esto activa las notificaciones automáticas