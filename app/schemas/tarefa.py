from typing import Optional
from enum import Enum
from datetime import date
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
    data_entrega: Optional[date] = None

class TarefaCreate(TarefaBase):
    pass

class TarefaResponse(TarefaBase):
    id: int
    atrasada: bool
    
    class Config:
        from_attributes = True

class TarefaUpdate(BaseModel):
    nome: str
    descricao: str
    status: bool
    prioridade: Prioridade
    data_entrega: Optional[date] = None