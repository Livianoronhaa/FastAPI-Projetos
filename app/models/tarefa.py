from enum import Enum as PythonEnum
from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, Enum
from app.database import Base
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
        server_default='baixa',
        nullable=False
    )