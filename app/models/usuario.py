from sqlalchemy import Column, Integer, String
from app.database import Base
from sqlalchemy.orm import relationship

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    senha_hash = Column(String)

    projetos = relationship("Projeto", back_populates="criador")   
    projetos_compartilhados = relationship("ProjetoCompartilhado", back_populates="usuario")