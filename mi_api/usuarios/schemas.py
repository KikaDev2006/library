from pydantic import BaseModel, EmailStr, ConfigDict, field_serializer, field_validator
from datetime import datetime

class UsuarioIn(BaseModel):
    nombre: str
    email: EmailStr
    contraseña: str
    imagen: str | None = None

class UsuarioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nombre: str
    email: EmailStr
    imagen: str | None = None
    fecha_registro: datetime

    @field_validator('imagen', mode='before')
    def validate_imagen(cls, value):
        if value is None:
            return None
        return str(value)

    @field_serializer('imagen')
    def serialize_imagen(self, value):
        return str(value) if value else None

class UsuarioUpdate(BaseModel):
    nombre: str | None = None
    imagen: str | None = None
    contraseña: str | None = None


class PasswordUpdateSchema(BaseModel):
    nueva_contraseña: str
    
