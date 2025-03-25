from pydantic import BaseModel, EmailStr
from enum import Enum 

class UsuarioBase(BaseModel):
    nome: str
    email: EmailStr

class UsuarioCreate(UsuarioBase):
    senha: str

class UsuarioResponse(UsuarioBase):
    id: int

    class Config:
        from_attributes = True


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


class Prioridade(str, Enum):
    baixa = "baixa"
    media = "media"
    alta = "alta"
       
class TarefaBase(BaseModel):
    nome: str
    descricao: str
    status: bool = False
    projeto_id: int
    usuario_id: int
    prioridade: Prioridade = Prioridade.baixa

class TarefaCreate(TarefaBase):
    pass

class TarefaResponse(TarefaBase):
    id: int

    class Config:
        from_attributes = True

        from pydantic import BaseModel

class TarefaUpdate(BaseModel):
    nome: str
    descricao: str
    status: bool

    
class Mensagem(BaseModel):
    mensagem: str
