from sqlalchemy import Enum, Column, Integer, String, Text, Boolean, ForeignKey
from .database import Base
from enum import Enum as PythonEnum

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    senha_hash = Column(String)

class Projeto(Base):
    __tablename__ = "projetos"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    descricao = Column(Text, nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False) 


class Prioridade(str, PythonEnum):
    BAIXA = 'baixa'
    MEDIA = 'media'
    ALTA = 'alta'
    
class Tarefa(Base):
    __tablename__ = "tarefas"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    descricao = Column(Text, nullable=False)
    status = Column(Boolean, default=False)
    projeto_id = Column(Integer, ForeignKey("projetos.id"), nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    prioridade = Column(
        Enum('baixa', 'media', 'alta', name='prioridade_enum'),
        server_default='baixa',  # Mude default para server_default
        nullable=False
    )