import datetime

from ninja import Schema

from ninja import Schema

# Datos que recibes al crear usuario
class UsuarioIn(Schema):
    username: str
    password: str
    email: str | None = None
    

# Datos que devuelves al cliente (sin mostrar la contraseña)
class UsuarioOut(Schema):
    id: int
    username: str
    email: str | None = None
    fecha_registro: datetime.datetime | None = None
    
class LoginIn(Schema):
    email: str
    password: str

class LoginOut(Schema):
    token: str
