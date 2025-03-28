from sqlalchemy import Column, Integer, String, Text, ForeignKey
from app.database import Base
from sqlalchemy.orm import relationship

class Projeto(Base):
    __tablename__ = "projetos"
    
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    descricao = Column(Text, nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)

    criador = relationship("Usuario", back_populates="projetos")
    compartilhamentos = relationship("ProjetoCompartilhado", back_populates="projeto")

class ProjetoCompartilhado(Base):
    __tablename__ = "projetos_compartilhados"
    
    id = Column(Integer, primary_key=True, index=True)
    projeto_id = Column(Integer, ForeignKey("projetos.id"))
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    permissoes = Column(String)
    
    projeto = relationship("Projeto", back_populates="compartilhamentos")
    usuario = relationship("Usuario", back_populates="projetos_compartilhados")