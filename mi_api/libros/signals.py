# libros/signals.py - VERSIÓN CON DEBUG

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Libro, Notificacion,Comentario

User = get_user_model()


@receiver(post_save, sender=Libro)
def enviar_notificacion_libro(sender, instance, created, **kwargs):
    print("=" * 50)
    print("🔔 SEÑAL ACTIVADA")
    print(f"📚 Libro: {instance.titulo}")
    print(f"👤 Autor: {instance.autor.username}")
    print(f"🔓 Visibilidad: {instance.visibilidad}")
    print(f"✨ ¿Creado? {created}")
    print("=" * 50)
    
    # Solo si el libro es público
    if instance.visibilidad != "publico":
        print("❌ Libro no es público - No se crean notificaciones")
        return
    
    # Verificar si ya hay notificación
    if Notificacion.objects.filter(libro_id=instance.id).exists():
        print("⚠️ Ya existe notificación para este libro")
        return
    
    # Obtener TODOS los usuarios (menos el autor)
    usuarios = User.objects.exclude(id=instance.autor.id).filter(notificaciones_activas=True)  # 👈 agregado el filter
    print(f"👥 Usuarios a notificar: {usuarios.count()}")
    
    if not usuarios.exists():
        print("❌ No hay otros usuarios - No se crean notificaciones")
        return
    
    # Crear mensaje
    if created:
        tipo = 'nuevo_libro_publico'
        mensaje = f"📚 El libro '{instance.titulo}' fue creado por {instance.autor.username}"
    else:
        tipo = 'libro_actualizado'
        mensaje = f"📝 El libro '{instance.titulo}' fue actualizado por {instance.autor.username}"
    
    print(f"📝 Mensaje: {mensaje}")
    
    # Crear notificaciones
    notificaciones = []
    for usuario in usuarios:
        notificaciones.append(
            Notificacion(
                usuario=usuario,
                tipo=tipo,
                mensaje=mensaje,
                libro_id=instance.id,
                titulo_libro=instance.titulo,
                autor_nombre=instance.autor.username,
                autor_id=instance.autor.id,
            )
        )
    
    if notificaciones:
        Notificacion.objects.bulk_create(notificaciones)
        print(f"✅ {len(notificaciones)} notificaciones creadas!")
    else:
        print("❌ No se crearon notificaciones")
    
    print("=" * 50)
    
    
# Signals para notificar el usuario dueño del libro cuando se crea un nuevo comentario
from .models import Libro, Notificacion, Comentario  # 👈 agregá Comentario al import existente


@receiver(post_save, sender=Comentario)
def enviar_notificacion_comentario(sender, instance, created, **kwargs):
    print("=" * 50)
    print("💬 SEÑAL DE COMENTARIO ACTIVADA")

    # Solo notificar cuando se crea el comentario, no cuando se edita
    if not created:
        print("❌ No es un comentario nuevo - No se notifica")
        return

    autor_libro = instance.libro.autor

    # No notificar si el autor comenta su propio libro
    if instance.usuario_id == autor_libro.id:
        print("❌ El autor comentó su propio libro - No se notifica")
        return
    
    if not autor_libro.notificaciones_activas:
        print("🔕 El usuario tiene las notificaciones apagadas")
        return

    mensaje = f"💬 {instance.usuario.username} comentó en tu libro '{instance.libro.titulo}'"
    print(f"📝 Mensaje: {mensaje}")

    Notificacion.objects.create(
        usuario=autor_libro,
        tipo='nuevo_comentario',
        mensaje=mensaje,
        libro_id=instance.libro.id,
        titulo_libro=instance.libro.titulo,
        autor_nombre=instance.usuario.username,
        autor_id=instance.usuario.id,
    )
    print("✅ Notificación de comentario creada!")
    print("=" * 50)