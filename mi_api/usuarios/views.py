from ninja import Router
from .models import Usuario
from .schemas import PasswordUpdateSchema, UsuarioIn, UsuarioOut, UsuarioUpdate




router = Router()

@router.get("/", response=list[UsuarioOut])
def listar_usuarios(request):
    return list(Usuario.objects.all())

@router.get("/{usuario_id}", response=UsuarioOut)
def obtener_usuario(request, usuario_id: int):
    return Usuario.objects.get(id=usuario_id)

@router.post("/", response=UsuarioOut)
def crear_usuario(request, data: UsuarioIn):
    usuario = Usuario.objects.create(**data.model_dump())
    return usuario


@router.put("/{usuario_id}", response=UsuarioOut)
def actualizar_usuario(request, usuario_id: int, data: UsuarioUpdate):
    usuario = Usuario.objects.get(id=usuario_id)
    for campo, valor in data.model_dump(exclude_unset=True).items():
        setattr(usuario, campo, valor)
    usuario.save()
    return usuario


@router.put("/{usuario_id}/password", response=PasswordUpdateSchema)
def actualizar_contraseña(request, usuario_id: int, nueva_contraseña: str):
    usuario = Usuario.objects.get(id=usuario_id)
    usuario.contraseña = nueva_contraseña
    usuario.save()
    return {"nueva_contraseña": nueva_contraseña}


@router.delete("/{usuario_id}", response=dict)
def eliminar_usuario(request, usuario_id: int):
    usuario = Usuario.objects.get(id=usuario_id)
    usuario.delete()
    return {"mensaje": "Usuario eliminado"}


# Create your views here.
