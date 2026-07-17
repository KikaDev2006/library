from ninja.errors import HttpError

MAX_PORTADA_MB = 5
MAX_ARCHIVO_MB = 50

EXTENSIONES_PORTADA = (".jpg", ".jpeg", ".png", ".webp")
EXTENSIONES_ARCHIVO = (".pdf", ".epub")

FIRMA_PDF = b"%PDF-"
FIRMA_ZIP = b"PK\x03\x04"  # epub es internamente un .zip


def _extension_valida(nombre: str, extensiones: tuple[str, ...]) -> bool:
    return nombre.lower().endswith(extensiones)


def _leer_cabecera(file_obj, n: int = 16) -> bytes:
    pos = file_obj.tell()
    file_obj.seek(0)
    cabecera = file_obj.read(n)
    file_obj.seek(pos)
    return cabecera


def validar_portada(portada):
    if not portada:
        return

    if not _extension_valida(portada.name, EXTENSIONES_PORTADA):
        raise HttpError(400, "La portada debe ser una imagen (jpg, jpeg, png, webp)")

    if portada.size == 0:
        raise HttpError(400, "La portada está vacía")

    if portada.size > MAX_PORTADA_MB * 1024 * 1024:
        raise HttpError(400, f"La portada no puede superar {MAX_PORTADA_MB}MB")

    cabecera = _leer_cabecera(portada)
    es_jpg = cabecera.startswith(b"\xff\xd8\xff")
    es_png = cabecera.startswith(b"\x89PNG\r\n\x1a\n")
    es_webp = cabecera.startswith(b"RIFF") and cabecera[8:12] == b"WEBP"

    if not (es_jpg or es_png or es_webp):
        raise HttpError(
            400,
            "El contenido del archivo no coincide con una imagen válida (jpg/png/webp)",
        )


def validar_archivo_libro(archivo):
    if not archivo:
        return

    if not _extension_valida(archivo.name, EXTENSIONES_ARCHIVO):
        raise HttpError(400, "El archivo debe ser .pdf o .epub")

    if archivo.size == 0:
        raise HttpError(400, "El archivo está vacío")

    if archivo.size > MAX_ARCHIVO_MB * 1024 * 1024:
        raise HttpError(400, f"El archivo no puede superar {MAX_ARCHIVO_MB}MB")

    cabecera = _leer_cabecera(archivo)
    nombre = archivo.name.lower()

    if nombre.endswith(".pdf") and not cabecera.startswith(FIRMA_PDF):
        raise HttpError(400, "El contenido del archivo no coincide con un PDF válido")

    if nombre.endswith(".epub") and not cabecera.startswith(FIRMA_ZIP):
        raise HttpError(400, "El contenido del archivo no coincide con un EPUB válido")