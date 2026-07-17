# utils.py - Funciones de utilidad para sanitización

import bleach
import re


def sanitizar_contenido_tiptap(contenido: str) -> str:
    """
    Sanitizar contenido HTML generado por Tiptap.
    Permite las etiquetas y atributos seguros para el editor.
    """
    if not contenido:
        return contenido
    
    # Etiquetas permitidas por Tiptap
    allowed_tags = [
        'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'strong', 'b', 'em', 'i', 'u', 's', 'strike',
        'a', 'ul', 'ol', 'li', 'blockquote',
        'code', 'pre', 'br', 'hr',
        'img', 'iframe', 'table', 'thead', 'tbody',
        'tr', 'th', 'td', 'caption'
    ]
    
    # Atributos permitidos por Tiptap
    allowed_attrs = {
        'a': ['href', 'target', 'rel', 'class'],
        'img': ['src', 'alt', 'width', 'height', 'class'],
        'iframe': ['src', 'width', 'height', 'frameborder', 'allowfullscreen'],
        'p': ['class', 'style'],
        'h1': ['class'], 'h2': ['class'], 'h3': ['class'],
        'h4': ['class'], 'h5': ['class'], 'h6': ['class'],
        'table': ['class'], 'td': ['colspan', 'rowspan', 'style'],
        'th': ['colspan', 'rowspan', 'style'],
        'pre': ['class'],
        'code': ['class'],
        'ul': ['class'], 'ol': ['class'], 'li': ['class'],
        'blockquote': ['class']
    }
    
    # Limpiar el HTML
    cleaned = bleach.clean(
        contenido,
        tags=allowed_tags,
        attributes=allowed_attrs,
        strip=True,
        strip_comments=True
    )
    
    # Eliminar estilos peligrosos (como position: fixed, etc.)
    # Esto es una medida extra de seguridad
    cleaned = re.sub(
        r'style\s*=\s*["\']([^"\']*position\s*:\s*(fixed|absolute)[^"\']*)["\']',
        '',
        cleaned,
        flags=re.IGNORECASE
    )
    
    return cleaned


def validar_contenido_seguro(contenido: str) -> bool:
    """
    Validar que el contenido no tenga scripts o estilos peligrosos
    """
    # Buscar scripts
    if re.search(r'<script', contenido, re.IGNORECASE):
        return False
    
    # Buscar eventos onclick, onload, etc.
    if re.search(r'on\w+\s*=', contenido, re.IGNORECASE):
        return False
    
    return True