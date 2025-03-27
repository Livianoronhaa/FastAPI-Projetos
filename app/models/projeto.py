from sqlalchemy import Column, Integer, String, Text, ForeignKey
from app.database import Base
class Projeto(Base):
    __tablename__ = "projetos"
    
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    descricao = Column(Text, nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)