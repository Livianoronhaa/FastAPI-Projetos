from enum import Enum
from pydantic import BaseModel
from .projeto import ProjetoResponse
from .usuario import UsuarioResponse

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

class TarefaUpdate(BaseModel):
    nome: str
    descricao: str
    status: bool
    prioridade: Prioridade