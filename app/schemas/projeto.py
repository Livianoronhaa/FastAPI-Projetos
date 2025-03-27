from pydantic import BaseModel
from .usuario import UsuarioResponse

class ProjetoBase(BaseModel):
    nome: str
    descricao: str
    usuario_id: int

class ProjetoCreate(ProjetoBase):
    pass

class ProjetoResponse(ProjetoBase):
    id: int

    class Config:
        from_attributes = True

class ProjetoUpdate(BaseModel):
    nome: str
    descricao: str