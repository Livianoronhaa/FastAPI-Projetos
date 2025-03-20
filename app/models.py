from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey
from .database import Base

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


class Tarefa(Base):
    __tablename__ = "tarefas"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    descricao = Column(Text, nullable=False)
    status = Column(Boolean, default=False)
    projeto_id = Column(Integer, ForeignKey("projetos.id"), nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)