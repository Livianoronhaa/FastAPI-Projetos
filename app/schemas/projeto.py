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



class ProjetoCompartilhadoCreate(BaseModel):
    usuario_email: str
    permissoes: str

class ProjetoCompartilhado(BaseModel):
    id: int
    projeto_id: int
    usuario_id: int
    permissoes: str

    class Config:
        orm_mode = True